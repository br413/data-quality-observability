from datetime import datetime, timezone

from src.dqo.history import HistoryStore
from src.dqo.models import CheckResult, CheckStatus, RunSummary, Severity


def _sample_summary(run_id: str) -> RunSummary:
    return RunSummary(
        contract_name="orders",
        run_id=run_id,
        started_at=datetime(2026, 7, 14, 10, 0, tzinfo=timezone.utc),
        finished_at=datetime(2026, 7, 14, 10, 1, tzinfo=timezone.utc),
        results=(
            CheckResult(
                contract_name="orders",
                check_type="schema",
                status=CheckStatus.PASSED,
                message="ok",
                severity=Severity.INFO,
            ),
            CheckResult(
                contract_name="orders",
                check_type="nulls",
                status=CheckStatus.FAILED,
                message="missing values",
                severity=Severity.CRITICAL,
                failed_count=1,
            ),
        ),
    )


def test_history_store_persists_runs(tmp_path) -> None:
    db_url = f"sqlite:///{tmp_path / 'history.db'}"
    store = HistoryStore(database_url=db_url)
    store.save_run(_sample_summary("run-1"))

    runs = store.recent_runs("orders")
    assert len(runs) == 1
    assert runs[0]["run_id"] == "run-1"
    assert runs[0]["passed"] == 0

    failures = store.failure_trend("orders")
    assert len(failures) == 1
    assert failures[0].check_type == "nulls"
