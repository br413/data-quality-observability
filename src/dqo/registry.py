"""Resolve contract names via contracts/registry.yml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_registry(registry_path: Path) -> dict[str, Any]:
    if not registry_path.is_file():
        raise FileNotFoundError(f"Contract registry not found: {registry_path}")

    payload = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("registry file must be a mapping")

    contracts = payload.get("contracts")
    if not isinstance(contracts, dict):
        raise ValueError("registry contracts section must be a mapping")

    return contracts


def resolve_contract_path(
    name_or_path: str | Path,
    *,
    registry_path: Path = Path("contracts/registry.yml"),
    contracts_dir: Path = Path("contracts"),
) -> Path:
    candidate = Path(name_or_path)

    if candidate.suffix == ".yml":
        if candidate.is_file():
            return candidate
        nested = contracts_dir / candidate.name
        if nested.is_file():
            return nested

    contract_key = str(name_or_path)
    registry = load_registry(registry_path)
    entry = registry.get(contract_key)
    if not isinstance(entry, dict):
        raise ValueError(
            f"Unknown contract '{contract_key}'. "
            f"Use a registry name or path to a .yml file under {contracts_dir}/"
        )

    relative_path = entry.get("path")
    if not isinstance(relative_path, str):
        raise ValueError(f"Registry entry for '{contract_key}' is missing a path")

    resolved = contracts_dir / relative_path
    if not resolved.is_file():
        raise FileNotFoundError(f"Contract file for '{contract_key}' not found: {resolved}")

    return resolved
