from pathlib import Path

from src.dqo.cli import main


def test_cli_run_passes_with_reference_time(tmp_path: Path) -> None:
    exit_code = main(
        [
            "run",
            "--contract",
            "contracts/orders.yml",
            "--data",
            "data/samples/orders.csv",
            "--references",
            "data/samples",
            "--reference-time",
            "2026-07-14T12:00:00Z",
            "--no-console-alerts",
            "--history-db",
            f"sqlite:///{tmp_path / 'history.db'}",
        ]
    )

    assert exit_code == 0
