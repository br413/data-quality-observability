"""Persist check run history."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from src.dqo.models import CheckResult, CheckStatus, RunSummary, Severity


class HistoryStore:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or os.environ.get(
            "DQO_DATABASE_URL",
            "sqlite:///.dqo/history.db",
        )
        self._is_sqlite = self.database_url.startswith("sqlite:///")
        self._ensure_schema()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        if self._is_sqlite:
            db_path = Path(self.database_url.replace("sqlite:///", "", 1))
            db_path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(db_path)
        elif self.database_url.startswith("postgresql://"):
            import psycopg

            connection = psycopg.connect(self.database_url)
        else:
            raise ValueError(f"unsupported database url: {self.database_url}")

        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _execute(self, connection, query: str, params: tuple[object, ...]) -> None:
        if self._is_sqlite:
            connection.execute(query.replace("%s", "?"), params)
            return
        connection.execute(query, params)

    def _query(self, connection, query: str, params: tuple[object, ...]):
        if self._is_sqlite:
            return connection.execute(query.replace("%s", "?"), params)
        return connection.execute(query, params)

    def _ensure_schema(self) -> None:
        with self._connection() as connection:
            if self._is_sqlite:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS check_runs (
                        run_id TEXT PRIMARY KEY,
                        contract_name TEXT NOT NULL,
                        started_at TEXT NOT NULL,
                        finished_at TEXT NOT NULL,
                        passed INTEGER NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS check_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        run_id TEXT NOT NULL,
                        check_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        row_count INTEGER,
                        failed_count INTEGER,
                        metadata_json TEXT,
                        FOREIGN KEY(run_id) REFERENCES check_runs(run_id)
                    )
                    """
                )
            else:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS check_runs (
                        run_id TEXT PRIMARY KEY,
                        contract_name TEXT NOT NULL,
                        started_at TIMESTAMPTZ NOT NULL,
                        finished_at TIMESTAMPTZ NOT NULL,
                        passed BOOLEAN NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS check_results (
                        id SERIAL PRIMARY KEY,
                        run_id TEXT NOT NULL REFERENCES check_runs(run_id),
                        check_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        row_count INTEGER,
                        failed_count INTEGER,
                        metadata_json TEXT
                    )
                    """
                )

    def save_run(self, summary: RunSummary) -> None:
        with self._connection() as connection:
            self._execute(
                connection,
                """
                INSERT INTO check_runs (run_id, contract_name, started_at, finished_at, passed)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    summary.run_id,
                    summary.contract_name,
                    summary.started_at.isoformat(),
                    summary.finished_at.isoformat(),
                    summary.passed if not self._is_sqlite else int(summary.passed),
                ),
            )

            for result in summary.results:
                self._execute(
                    connection,
                    """
                    INSERT INTO check_results (
                        run_id, check_type, status, severity, message,
                        row_count, failed_count, metadata_json
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        summary.run_id,
                        result.check_type,
                        result.status.value,
                        result.severity.value,
                        result.message,
                        result.row_count,
                        result.failed_count,
                        json.dumps(result.metadata),
                    ),
                )

    def recent_runs(self, contract_name: str, *, limit: int = 10) -> list[dict[str, object]]:
        with self._connection() as connection:
            cursor = self._query(
                connection,
                """
                SELECT run_id, contract_name, started_at, finished_at, passed
                FROM check_runs
                WHERE contract_name = %s
                ORDER BY started_at DESC
                LIMIT %s
                """,
                (contract_name, limit),
            )
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def failure_trend(self, contract_name: str, *, limit: int = 20) -> list[CheckResult]:
        with self._connection() as connection:
            cursor = self._query(
                connection,
                """
                SELECT cr.check_type, cr.status, cr.severity, cr.message,
                       cr.row_count, cr.failed_count, cr.metadata_json, runs.contract_name
                FROM check_results cr
                JOIN check_runs runs ON runs.run_id = cr.run_id
                WHERE runs.contract_name = %s AND cr.status = %s
                ORDER BY runs.started_at DESC
                LIMIT %s
                """,
                (contract_name, CheckStatus.FAILED.value, limit),
            )

            results: list[CheckResult] = []
            for row in cursor.fetchall():
                metadata = json.loads(row[6] or "{}")
                results.append(
                    CheckResult(
                        contract_name=row[7],
                        check_type=row[0],
                        status=CheckStatus(row[1]),
                        severity=Severity(row[2]),
                        message=row[3],
                        row_count=row[4],
                        failed_count=row[5],
                        metadata=metadata,
                    )
                )
            return results
