"""Run quality checks for a contract-bound dataset."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.dqo.checks.freshness import validate_freshness
from src.dqo.checks.nulls import validate_nulls
from src.dqo.checks.referential import validate_referential_integrity
from src.dqo.checks.schema import validate_schema
from src.dqo.checks.uniqueness import validate_uniqueness
from src.dqo.contracts import load_contract
from src.dqo.dataset import load_csv
from src.dqo.models import CheckResult, DataContract, RunSummary


def run_checks(
    contract: DataContract,
    rows: list[dict[str, str]],
    *,
    reference_tables: dict[str, list[dict[str, str]]] | None = None,
    now: datetime | None = None,
) -> tuple[CheckResult, ...]:
    references = reference_tables or {}
    return (
        validate_schema(contract, rows),
        validate_nulls(contract, rows),
        validate_uniqueness(contract, rows),
        validate_freshness(contract, rows, now=now),
        validate_referential_integrity(contract, rows, references),
    )


def run_contract_file(
    contract_path: Path,
    dataset_path: Path,
    *,
    reference_dir: Path | None = None,
    now: datetime | None = None,
) -> RunSummary:
    started_at = datetime.now(timezone.utc)
    contract = load_contract(contract_path)
    rows = load_csv(dataset_path)

    references: dict[str, list[dict[str, str]]] = {}
    if reference_dir is not None:
        for csv_path in sorted(reference_dir.glob("*.csv")):
            references[csv_path.stem] = load_csv(csv_path)

    results = run_checks(contract, rows, reference_tables=references, now=now)
    finished_at = datetime.now(timezone.utc)

    return RunSummary(
        contract_name=contract.name,
        run_id=str(uuid.uuid4()),
        started_at=started_at,
        finished_at=finished_at,
        results=results,
    )
