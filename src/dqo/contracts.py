"""Load and validate data contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.dqo.models import (
    ColumnContract,
    DataContract,
    ForeignKeyContract,
    FreshnessContract,
)


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def load_contract(path: Path) -> DataContract:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    document = _require_mapping(payload, "contract file")

    columns_section = _require_mapping(document.get("columns"), "columns")
    columns = tuple(
        ColumnContract(
            name=name,
            type=str(spec["type"]),
            nullable=bool(spec.get("nullable", True)),
            unique=bool(spec.get("unique", False)),
        )
        for name, spec in columns_section.items()
    )

    foreign_keys: list[ForeignKeyContract] = []
    for entry in document.get("referential_integrity", []):
        mapping = _require_mapping(entry, "referential_integrity entry")
        references = _require_mapping(mapping.get("references"), "references")
        foreign_keys.append(
            ForeignKeyContract(
                column=str(mapping["column"]),
                references_table=str(references["table"]),
                references_column=str(references["column"]),
            )
        )

    freshness = None
    if "freshness" in document:
        freshness_spec = _require_mapping(document["freshness"], "freshness")
        freshness = FreshnessContract(
            column=str(freshness_spec["column"]),
            max_age_hours=int(freshness_spec["max_age_hours"]),
        )

    return DataContract(
        name=str(document["name"]),
        version=str(document["version"]),
        description=str(document.get("description", "")),
        columns=columns,
        foreign_keys=tuple(foreign_keys),
        freshness=freshness,
    )
