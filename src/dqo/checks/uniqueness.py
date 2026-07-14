"""Uniqueness checks."""

from __future__ import annotations

from collections import Counter

from src.dqo.models import CheckResult, CheckStatus, DataContract, Severity


def validate_uniqueness(contract: DataContract, rows: list[dict[str, str]]) -> CheckResult:
    unique_columns = [column.name for column in contract.columns if column.unique]
    duplicates: list[str] = []

    for column_name in unique_columns:
        values = [row[column_name] for row in rows]
        counts = Counter(values)
        repeated = [value for value, count in counts.items() if count > 1]
        if repeated:
            duplicates.append(f"{column_name} duplicates: {', '.join(repeated[:5])}")

    if duplicates:
        return CheckResult(
            contract_name=contract.name,
            check_type="uniqueness",
            status=CheckStatus.FAILED,
            message="; ".join(duplicates),
            severity=Severity.CRITICAL,
            row_count=len(rows),
            failed_count=len(duplicates),
        )

    return CheckResult(
        contract_name=contract.name,
        check_type="uniqueness",
        status=CheckStatus.PASSED,
        message="unique columns have no duplicates",
        severity=Severity.INFO,
        row_count=len(rows),
    )
