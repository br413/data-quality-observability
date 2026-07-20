"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.dqo.alerts import AlertRouter, ConsoleAlertChannel, FileAlertChannel, WebhookAlertChannel
from src.dqo.history import HistoryStore
from src.dqo.runner import run_contract_file


def _parse_reference_time(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run data-quality checks against contracts")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Execute checks for a contract")
    run_parser.add_argument("--contract", required=True, type=Path)
    run_parser.add_argument("--data", required=True, type=Path)
    run_parser.add_argument("--references", type=Path, default=None)
    run_parser.add_argument("--history-db", type=str, default=None)
    run_parser.add_argument("--alert-file", type=Path, default=Path(".dqo/alerts.jsonl"))
    run_parser.add_argument("--webhook-url", type=str, default=None)
    run_parser.add_argument("--no-console-alerts", action="store_true")
    run_parser.add_argument(
        "--reference-time",
        type=_parse_reference_time,
        default=None,
        help="Evaluate freshness relative to this ISO-8601 timestamp (default: current UTC time)",
    )

    history_parser = subparsers.add_parser("history", help="Show recent runs")
    history_parser.add_argument("--contract", required=True)
    history_parser.add_argument("--limit", type=int, default=10)
    history_parser.add_argument("--history-db", type=str, default=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        summary = run_contract_file(
            args.contract,
            args.data,
            reference_dir=args.references,
            now=args.reference_time,
        )

        store = HistoryStore(database_url=args.history_db)
        store.save_run(summary)

        channels = []
        if not args.no_console_alerts:
            channels.append(ConsoleAlertChannel())
        channels.append(FileAlertChannel(args.alert_file))
        if args.webhook_url:
            channels.append(WebhookAlertChannel(args.webhook_url))

        AlertRouter(channels).route(summary)

        for result in summary.results:
            print(f"{result.check_type:22} {result.status.value:7} {result.message}")

        return 0 if summary.passed else 1

    if args.command == "history":
        store = HistoryStore(database_url=args.history_db)
        runs = store.recent_runs(args.contract, limit=args.limit)
        for run in runs:
            status = "passed" if run["passed"] else "failed"
            print(f"{run['started_at']}  {run['run_id']}  {status}")
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
