from pathlib import Path

import pytest

from src.dqo.registry import validate_registry


def test_registry_paths_versions_and_changelog_align() -> None:
    errors = validate_registry()
    assert errors == []


def test_validate_registry_detects_version_mismatch(tmp_path: Path) -> None:
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir()
    registry_path = contracts_dir / "registry.yml"
    changelog_path = contracts_dir / "CHANGELOG.md"

    registry_path.write_text(
        """
contracts:
  orders:
    current: "2.0"
    path: orders.yml
""".strip(),
        encoding="utf-8",
    )
    (contracts_dir / "orders.yml").write_text(
        """
name: orders
version: "1.0"
description: test
columns:
  order_id:
    type: string
    nullable: false
""".strip(),
        encoding="utf-8",
    )
    changelog_path.write_text(
        """
## orders

### 1.0 (initial)
- test
""".strip(),
        encoding="utf-8",
    )

    errors = validate_registry(
        registry_path=registry_path,
        contracts_dir=contracts_dir,
        changelog_path=changelog_path,
    )
    assert any("registry current '2.0'" in error for error in errors)
    assert any("missing '### 2.0'" in error for error in errors)
