"""Nullability checks."""

from __future__ import annotations

from src.dqo.models import CheckResult, CheckStatus, DataContract, Severity


def validate_nulls(contract: DataContract, rows: list[dict[str, str]]) -> CheckResult:
    non_nullable = [column.name for column in contract.columns if not column.nullable]
    violations: list[str] = []

    for column_name in non_nullable:
        null_rows = [index for index, row in enumerate(rows) if not str(row.get(column_name, "")).strip()]
        if null_rows:
            violations.append(f"{column_name} null at rows {null_rows[:5]}")

    if violations:
        return CheckResult(
            contract_name=contract.name,
            check_type="nulls",
            status=CheckStatus.FAILED,
            message="; ".join(violations),
            severity=Severity.CRITICAL,
            row_count=len(rows),
            failed_count=len(violations),
        )

    return CheckResult(
        contract_name=contract.name,
        check_type="nulls",
        status=CheckStatus.PASSED,
        message="required columns are populated",
        severity=Severity.INFO,
        row_count=len(rows),
    )
