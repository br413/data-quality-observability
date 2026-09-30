"""A reproducible broken-to-fixed walkthrough shipped inside the package."""

from datetime import datetime, timezone
from importlib.resources import files
from pathlib import Path

from .history import HistoryStore
from .report import write_report
from .runner import run_contract_file

REFERENCE_TIME = datetime(2026, 7, 14, 12, tzinfo=timezone.utc)


def create_demo(output: Path) -> Path:
    # Never replace a user's existing demo or data files.
    output.mkdir(parents=True, exist_ok=False)
    examples = files(__package__).joinpath("examples")
    for name in ("orders.yml", "orders.csv", "orders_invalid.csv", "customers.csv"):
        output.joinpath(name).write_text(examples.joinpath(name).read_text(encoding="utf-8"), encoding="utf-8")
    summaries = [
        run_contract_file(output / "orders.yml", output / name, reference_dir=output, now=REFERENCE_TIME)
        for name in ("orders_invalid.csv", "orders.csv")
    ]
    if summaries[0].passed or not summaries[1].passed:
        raise RuntimeError("demo invariant failed: expected a failing run followed by a passing run")
    store = HistoryStore(f"sqlite:///{(output / 'history.db').resolve().as_posix()}")
    for summary in summaries:
        store.save_run(summary)
    report = output / "report.html"
    write_report(report, summaries, title="From broken data to a clean run")
    write_report(output / "report.json", summaries)
    return report
