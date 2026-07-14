"""Referential integrity checks."""

from __future__ import annotations

from src.dqo.models import CheckResult, CheckStatus, DataContract, Severity


def validate_referential_integrity(
    contract: DataContract,
    rows: list[dict[str, str]],
    reference_tables: dict[str, list[dict[str, str]]],
) -> CheckResult:
    if not contract.foreign_keys:
        return CheckResult(
            contract_name=contract.name,
            check_type="referential_integrity",
            status=CheckStatus.SKIPPED,
            message="no referential integrity rules defined",
            severity=Severity.INFO,
            row_count=len(rows),
        )

    violations: list[str] = []

    for rule in contract.foreign_keys:
        reference_rows = reference_tables.get(rule.references_table)
        if reference_rows is None:
            return CheckResult(
                contract_name=contract.name,
                check_type="referential_integrity",
                status=CheckStatus.FAILED,
                message=f"missing reference table: {rule.references_table}",
                severity=Severity.CRITICAL,
                row_count=len(rows),
                failed_count=1,
            )

        valid_values = {row[rule.references_column] for row in reference_rows}
        orphan_values = sorted(
            {
                row[rule.column]
                for row in rows
                if row.get(rule.column) and row[rule.column] not in valid_values
            }
        )
        if orphan_values:
            violations.append(
                f"{rule.column} orphans ({rule.references_table}.{rule.references_column}): "
                f"{', '.join(orphan_values[:5])}"
            )

    if violations:
        return CheckResult(
            contract_name=contract.name,
            check_type="referential_integrity",
            status=CheckStatus.FAILED,
            message="; ".join(violations),
            severity=Severity.CRITICAL,
            row_count=len(rows),
            failed_count=len(violations),
        )

    return CheckResult(
        contract_name=contract.name,
        check_type="referential_integrity",
        status=CheckStatus.PASSED,
        message="foreign keys resolve to reference tables",
        severity=Severity.INFO,
        row_count=len(rows),
    )
