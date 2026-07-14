"""Freshness checks."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.dqo.models import CheckResult, CheckStatus, DataContract, Severity


def _parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def validate_freshness(
    contract: DataContract,
    rows: list[dict[str, str]],
    *,
    now: datetime | None = None,
) -> CheckResult:
    if contract.freshness is None:
        return CheckResult(
            contract_name=contract.name,
            check_type="freshness",
            status=CheckStatus.SKIPPED,
            message="no freshness contract defined",
            severity=Severity.INFO,
            row_count=len(rows),
        )

    if not rows:
        return CheckResult(
            contract_name=contract.name,
            check_type="freshness",
            status=CheckStatus.FAILED,
            message="cannot evaluate freshness on empty dataset",
            severity=Severity.WARNING,
            row_count=0,
            failed_count=1,
        )

    reference = now or datetime.now(timezone.utc)
    column_name = contract.freshness.column
    max_age = timedelta(hours=contract.freshness.max_age_hours)
    stale_rows: list[str] = []

    for row in rows:
        timestamp = _parse_datetime(row[column_name])
        if reference - timestamp > max_age:
            stale_rows.append(row.get("order_id") or row.get("customer_id") or column_name)

    if stale_rows:
        return CheckResult(
            contract_name=contract.name,
            check_type="freshness",
            status=CheckStatus.FAILED,
            message=(
                f"{len(stale_rows)} row(s) older than {contract.freshness.max_age_hours}h "
                f"on column {column_name}"
            ),
            severity=Severity.WARNING,
            row_count=len(rows),
            failed_count=len(stale_rows),
            metadata={"stale_sample": stale_rows[:5]},
        )

    return CheckResult(
        contract_name=contract.name,
        check_type="freshness",
        status=CheckStatus.PASSED,
        message=f"all rows within {contract.freshness.max_age_hours}h freshness window",
        severity=Severity.INFO,
        row_count=len(rows),
    )
