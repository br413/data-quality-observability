"""Shared domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class CheckStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class ColumnContract:
    name: str
    type: str
    nullable: bool = True
    unique: bool = False


@dataclass(frozen=True)
class ForeignKeyContract:
    column: str
    references_table: str
    references_column: str


@dataclass(frozen=True)
class FreshnessContract:
    column: str
    max_age_hours: int


@dataclass(frozen=True)
class DataContract:
    name: str
    version: str
    description: str
    columns: tuple[ColumnContract, ...]
    foreign_keys: tuple[ForeignKeyContract, ...] = ()
    freshness: FreshnessContract | None = None


@dataclass(frozen=True)
class CheckResult:
    contract_name: str
    check_type: str
    status: CheckStatus
    message: str
    severity: Severity
    row_count: int | None = None
    failed_count: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RunSummary:
    contract_name: str
    run_id: str
    started_at: datetime
    finished_at: datetime
    results: tuple[CheckResult, ...]

    @property
    def passed(self) -> bool:
        return all(result.status != CheckStatus.FAILED for result in self.results)

    @property
    def failed_results(self) -> tuple[CheckResult, ...]:
        return tuple(result for result in self.results if result.status == CheckStatus.FAILED)
