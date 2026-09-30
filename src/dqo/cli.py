"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .alerts import AlertRouter, ConsoleAlertChannel, FileAlertChannel, WebhookAlertChannel
from .demo import create_demo
from .history import HistoryStore
from .report import write_report
from .runner import run_contract_file


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
    run_parser.add_argument(
        "--contract",
        required=True,
        help="Registry contract name (e.g. orders) or path to contracts/*.yml",
    )
    run_parser.add_argument("--data", required=True, type=Path)
    run_parser.add_argument("--report", type=Path, help="Write an offline .html or machine-readable .json report")
    run_parser.add_argument("--references", type=Path, default=None)
    run_parser.add_argument("--registry", type=Path, default=Path("contracts/registry.yml"))
    run_parser.add_argument("--contracts-dir", type=Path, default=Path("contracts"))
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

    demo_parser = subparsers.add_parser("demo", help="Create a broken-to-fixed demo with an offline report")
    demo_parser.add_argument("--output", type=Path, default=Path("dqo-demo"), help="New output directory (must not already exist)")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return _execute(args)
    except (OSError, ValueError, KeyError, yaml.YAMLError) as exc:
        print(f"dqo: {exc}", file=sys.stderr)
        return 2


def _execute(args: argparse.Namespace) -> int:
    if args.command == "demo":
        report = create_demo(args.output)
        print("Demo complete: run 1 has intentional failures; run 2 passes.")
        print("Freshness is evaluated at 2026-07-14T12:00:00Z for repeatability.")
        print(f"Open {report.resolve().as_uri()}")
        return 0

    if args.command == "run":
        if args.report and args.report.suffix.lower() not in {".html", ".json"}:
            raise ValueError("report path must end in .html or .json")
        summary = run_contract_file(
            args.contract,
            args.data,
            reference_dir=args.references,
            now=args.reference_time,
            registry_path=args.registry,
            contracts_dir=args.contracts_dir,
        )

        store = HistoryStore(database_url=args.history_db)
        store.save_run(summary)
        if args.report:
            write_report(args.report, [summary])

        channels = []
        if not args.no_console_alerts:
            channels.append(ConsoleAlertChannel())
        channels.append(FileAlertChannel(args.alert_file))
        if args.webhook_url:
            channels.append(WebhookAlertChannel(args.webhook_url))

        AlertRouter(channels).route(summary)

        for result in summary.results:
            print(f"{result.check_type:22} {result.status.value:7} {result.message}")
        if args.report:
            print(f"Report: {args.report.resolve()}")

        return 0 if summary.passed else 1

    if args.command == "history":
        store = HistoryStore(database_url=args.history_db)
        runs = store.recent_runs(args.contract, limit=args.limit)
        for run in runs:
            status = "passed" if run["passed"] else "failed"
            version = run.get("contract_version") or "unknown"
            print(f"{run['started_at']}  {run['run_id']}  v{version}  {status}")
        return 0

    raise ValueError(f"unknown command: {args.command}")


if __name__ == "__main__":
    sys.exit(main())
