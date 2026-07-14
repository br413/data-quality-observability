from src.dqo.alerts import AlertRouter, ConsoleAlertChannel, FileAlertChannel
from src.dqo.models import CheckResult, CheckStatus, RunSummary, Severity
from datetime import datetime, timezone


def _failed_summary() -> RunSummary:
    return RunSummary(
        contract_name="orders",
        run_id="run-alert-1",
        started_at=datetime(2026, 7, 14, 10, 0, tzinfo=timezone.utc),
        finished_at=datetime(2026, 7, 14, 10, 1, tzinfo=timezone.utc),
        results=(
            CheckResult(
                contract_name="orders",
                check_type="nulls",
                status=CheckStatus.FAILED,
                message="missing order_total",
                severity=Severity.CRITICAL,
            ),
        ),
    )


def test_alert_router_writes_console_and_file(tmp_path, capsys) -> None:
    alert_file = tmp_path / "alerts.jsonl"
    router = AlertRouter([ConsoleAlertChannel(), FileAlertChannel(alert_file)])
    events = router.route(_failed_summary())

    assert len(events) == 1
    captured = capsys.readouterr()
    assert "CRITICAL" in captured.out
    assert alert_file.read_text(encoding="utf-8").strip()
