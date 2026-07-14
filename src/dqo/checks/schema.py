"""Schema validation against data contracts."""

from __future__ import annotations

from src.dqo.models import CheckResult, CheckStatus, DataContract, Severity


def validate_schema(contract: DataContract, rows: list[dict[str, str]]) -> CheckResult:
    expected = {column.name for column in contract.columns}
    if not rows:
        return CheckResult(
            contract_name=contract.name,
            check_type="schema",
            status=CheckStatus.PASSED,
            message="no rows to validate; schema contract loaded",
            severity=Severity.INFO,
            row_count=0,
        )

    actual = set(rows[0].keys())
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)

    if missing or unexpected:
        details: list[str] = []
        if missing:
            details.append(f"missing columns: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected columns: {', '.join(unexpected)}")
        return CheckResult(
            contract_name=contract.name,
            check_type="schema",
            status=CheckStatus.FAILED,
            message="; ".join(details),
            severity=Severity.CRITICAL,
            row_count=len(rows),
            failed_count=len(missing) + len(unexpected),
        )

    return CheckResult(
        contract_name=contract.name,
        check_type="schema",
        status=CheckStatus.PASSED,
        message="dataset columns match contract",
        severity=Severity.INFO,
        row_count=len(rows),
    )
