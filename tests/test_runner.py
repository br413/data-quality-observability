from datetime import datetime, timezone
from pathlib import Path

from src.dqo.runner import run_checks, run_contract_file


def test_run_checks_passes_for_valid_dataset(orders_contract, valid_orders, customers, fixed_now) -> None:
    results = run_checks(
        orders_contract,
        valid_orders,
        reference_tables={"customers": customers},
        now=fixed_now,
    )
    assert all(result.status.value != "failed" for result in results)


def test_run_contract_file_fails_for_invalid_dataset(tmp_path: Path) -> None:
    summary = run_contract_file(
        Path("contracts/orders.yml"),
        Path("data/samples/orders_invalid.csv"),
        reference_dir=Path("data/samples"),
        now=datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc),
    )
    assert summary.passed is False
    assert summary.failed_results
