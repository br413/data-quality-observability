"""Airflow DAG for scheduled data-quality contract checks."""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

DEFAULT_ARGS = {
    "owner": "br413",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

PROJECT_ROOT = os.environ.get("DQO_PROJECT_ROOT", os.getcwd())
HISTORY_DB = os.environ.get("DQO_DATABASE_URL", "sqlite:///.dqo/history.db")
ALERT_FILE = os.environ.get("DQO_ALERT_FILE", ".dqo/alerts.jsonl")
WEBHOOK_URL = os.environ.get("DQO_WEBHOOK_URL", "")

CHECK_COMMAND = (
    "python -m src.dqo.cli run "
    "--references data/samples "
    f"--history-db {HISTORY_DB} "
    f"--alert-file {ALERT_FILE} "
    "--no-console-alerts"
)
if WEBHOOK_URL:
    CHECK_COMMAND += f' --webhook-url "{WEBHOOK_URL}"'


def _contract_task(task_id: str, contract_name: str, dataset: str) -> BashOperator:
    return BashOperator(
        task_id=task_id,
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            f'echo "Running contract {contract_name} via registry" && '
            f"{CHECK_COMMAND} "
            f"--contract {contract_name} "
            f"--data data/samples/{dataset}"
        ),
    )


with DAG(
    dag_id="dqo_contract_checks",
    default_args=DEFAULT_ARGS,
    description="Run orders and customers contract checks via registry",
    schedule="@daily",
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=["data-quality", "contracts", "portfolio"],
    doc_md="""
    ## dqo_contract_checks

    Scheduled dataset contract checks resolved through `contracts/registry.yml`.

    1. **run_orders_checks** — `orders@1.0` against sample CSV
    2. **run_customers_checks** — `customers@1.0` against sample CSV

    Each task persists run history and appends alert JSONL. Set optional `DQO_WEBHOOK_URL`
    for webhook routing on failures (same pattern as `production-data-pipeline`).

    Environment:

    | Variable | Purpose |
    |----------|---------|
    | `DQO_PROJECT_ROOT` | Repository root on the Airflow worker |
    | `DQO_DATABASE_URL` | History store (SQLite default) |
    | `DQO_ALERT_FILE` | JSONL alert output path |
    | `DQO_WEBHOOK_URL` | Optional webhook for contract failures |

    See [ADR 0002](docs/adr/0002-schema-registry-and-contract-versioning.md) for registry design.
    """,
) as dag:
    run_orders_checks = _contract_task("run_orders_checks", "orders", "orders.csv")
    run_customers_checks = _contract_task("run_customers_checks", "customers", "customers.csv")

    run_orders_checks >> run_customers_checks
