"""Resolve contract names via contracts/registry.yml."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

from src.dqo.contracts import load_contract


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


def validate_registry(
    *,
    registry_path: Path = Path("contracts/registry.yml"),
    contracts_dir: Path = Path("contracts"),
    changelog_path: Path = Path("contracts/CHANGELOG.md"),
) -> list[str]:
    """Return human-readable errors when registry, contracts, or changelog disagree."""
    errors: list[str] = []
    registry = load_registry(registry_path)

    if not changelog_path.is_file():
        errors.append(f"changelog not found: {changelog_path}")
        changelog_text = ""
    else:
        changelog_text = changelog_path.read_text(encoding="utf-8")

    for name, entry in registry.items():
        if not isinstance(entry, dict):
            errors.append(f"{name}: registry entry must be a mapping")
            continue

        current = entry.get("current")
        relative_path = entry.get("path")
        if not isinstance(current, str):
            errors.append(f"{name}: registry entry missing string 'current'")
            continue
        if not isinstance(relative_path, str):
            errors.append(f"{name}: registry entry missing string 'path'")
            continue

        contract_path = contracts_dir / relative_path
        if not contract_path.is_file():
            errors.append(f"{name}: contract file not found at {contract_path}")
            continue

        contract = load_contract(contract_path)
        if contract.name != name:
            errors.append(
                f"{name}: registry key does not match contract name {contract.name!r}"
            )
        if contract.version != current:
            errors.append(
                f"{name}: registry current {current!r} != contract version {contract.version!r}"
            )

        if f"## {name}" not in changelog_text:
            errors.append(f"{name}: missing '## {name}' section in CHANGELOG")
            continue

        section = changelog_text.split(f"## {name}", 1)[1]
        next_heading = section.find("\n## ")
        if next_heading != -1:
            section = section[:next_heading]
        if f"### {current}" not in section:
            errors.append(
                f"{name}: CHANGELOG missing '### {current}' entry for current version"
            )

    return errors


def check_version_bump_discipline(base_ref: str) -> list[str]:
    """Fail when contract version changes without registry and CHANGELOG updates."""
    errors: list[str] = []
    changed = subprocess.run(
        ["git", "diff", "--name-only", base_ref, "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if changed.returncode != 0:
        return [f"git diff failed: {changed.stderr.strip()}"]

    changed_files = {line.strip() for line in changed.stdout.splitlines() if line.strip()}
    contract_files = [
        path
        for path in changed_files
        if path.startswith("contracts/")
        and path.endswith(".yml")
        and path != "contracts/registry.yml"
    ]
    if not contract_files:
        return []

    version_changed = False
    for contract_file in contract_files:
        patch = subprocess.run(
            ["git", "diff", base_ref, "HEAD", "--", contract_file],
            capture_output=True,
            text=True,
            check=False,
        )
        if patch.returncode != 0:
            errors.append(f"git diff failed for {contract_file}: {patch.stderr.strip()}")
            continue
        if re.search(r"^[-+]\s*version:", patch.stdout, re.MULTILINE):
            version_changed = True
            break

    if not version_changed:
        return errors

    if "contracts/registry.yml" not in changed_files:
        errors.append("contract version changed but contracts/registry.yml was not updated")
    if "contracts/CHANGELOG.md" not in changed_files:
        errors.append("contract version changed but contracts/CHANGELOG.md was not updated")

    return errors
