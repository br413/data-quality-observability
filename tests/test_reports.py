import json
import subprocess
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from src.dqo.cli import main
from src.dqo.demo import create_demo
from src.dqo.history import HistoryStore
from src.dqo.models import CheckStatus
from src.dqo.report import render_html
from src.dqo.runner import run_checks, run_contract_file

ROOT = Path(__file__).resolve().parents[1]


def test_demo_works_outside_checkout_and_preserves_existing_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["demo"]) == 0
    output = tmp_path / "dqo-demo"
    report = output / "report.html"
    original = report.read_bytes()
    payload = json.loads((output / "report.json").read_text())
    assert payload["schema_version"] == 1
    assert [run["passed"] for run in payload["runs"]] == [False, True]
    assert len(HistoryStore(f"sqlite:///{output / 'history.db'}").recent_runs("orders")) == 2
    assert main(["demo"]) == 2
    assert report.read_bytes() == original


def test_html_escapes_untrusted_contract_messages_and_metadata():
    summary = run_contract_file(
        ROOT / "contracts/orders.yml", ROOT / "data/samples/orders.csv",
        reference_dir=ROOT / "data/samples", now=datetime(2026, 7, 14, 12, tzinfo=timezone.utc),
    )
    attack = '<script>alert("x")</script>'
    result = replace(summary.results[0], message=attack, metadata={"sample": attack})
    html = render_html([replace(summary, contract_name=attack, results=(result,))], title=attack)
    assert attack not in html
    assert "&lt;script&gt;" in html
    assert "Content-Security-Policy" in html
    assert "<script" not in html


def test_failed_run_writes_json_and_returns_one(tmp_path):
    report = tmp_path / "report.json"
    assert main([
        "run", "--contract", str(ROOT / "contracts/orders.yml"),
        "--data", str(ROOT / "data/samples/orders_invalid.csv"),
        "--references", str(ROOT / "data/samples"),
        "--reference-time", "2026-07-14T12:00:00Z", "--report", str(report),
        "--history-db", f"sqlite:///{tmp_path / 'history.db'}",
        "--alert-file", str(tmp_path / "alerts.jsonl"), "--no-console-alerts",
    ]) == 1
    payload = json.loads(report.read_text())
    assert not payload["runs"][0]["passed"]
    assert sum(r["status"] == "failed" for r in payload["runs"][0]["results"]) == 4


def test_schema_failure_still_produces_a_report(orders_contract):
    results = run_checks(orders_contract, [{"wrong_column": "value"}])
    assert results[0].status == CheckStatus.FAILED
    assert all(r.status == CheckStatus.SKIPPED for r in results[1:])


def test_invalid_freshness_value_is_a_finding(orders_contract, valid_orders, customers, fixed_now):
    rows = [dict(row) for row in valid_orders]
    rows[0]["updated_at"] = "not a date"
    result = run_checks(orders_contract, rows, reference_tables={"customers": customers}, now=fixed_now)[3]
    assert result.status == CheckStatus.FAILED
    assert result.metadata["invalid_row_indices"] == [0]


def test_yaml_extension_and_missing_explicit_path(tmp_path):
    from src.dqo.registry import resolve_contract_path
    import pytest
    contract = tmp_path / "custom.yaml"
    contract.write_text("name: custom")
    assert resolve_contract_path(contract) == contract
    with pytest.raises(FileNotFoundError, match="Contract file not found"):
        resolve_contract_path(tmp_path / "orders.yml")


def test_bad_report_extension_fails_before_execution(tmp_path, capsys):
    assert main(["run", "--contract", "missing.yml", "--data", "missing.csv",
                 "--report", str(tmp_path / "report.txt")]) == 2
    assert "report path must end" in capsys.readouterr().err
    assert not (tmp_path / "report.txt").exists()


def test_installed_cli_demo_in_subprocess(tmp_path):
    result = subprocess.run([sys.executable, "-m", "dqo.cli", "demo"], cwd=tmp_path,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "dqo-demo/report.html").is_file()
