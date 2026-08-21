"""Validate contract registry consistency (ADR 0002 phase 4)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.dqo.registry import check_version_bump_discipline, validate_registry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate contracts/registry.yml consistency")
    parser.add_argument(
        "--base",
        default=None,
        help="Git ref for version-bump discipline check (e.g. origin/main)",
    )
    args = parser.parse_args(argv)

    errors = validate_registry()
    if args.base:
        errors.extend(check_version_bump_discipline(args.base))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("registry validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
