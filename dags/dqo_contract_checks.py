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

CHECK_COMMAND = (
    "python -m src.dqo.cli run "
    "--references data/samples "
    f"--history-db {HISTORY_DB} "
    f"--alert-file {ALERT_FILE} "
    "--no-console-alerts"
)

with DAG(
    dag_id="dqo_contract_checks",
    default_args=DEFAULT_ARGS,
    description="Run orders and customers contract checks",
    schedule="@daily",
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=["data-quality", "contracts", "portfolio"],
    doc_md="""
    ## dqo_contract_checks

    1. Execute orders and customers YAML contract checks
    2. Persist run history and route alerts to JSONL

    Set `DQO_PROJECT_ROOT` to the repository root when deploying.
    """,
) as dag:
    run_orders_checks = BashOperator(
        task_id="run_orders_checks",
        bash_command=(
            f"cd {PROJECT_ROOT} && {CHECK_COMMAND} "
            "--contract contracts/orders.yml "
            "--data data/samples/orders.csv"
        ),
    )

    run_customers_checks = BashOperator(
        task_id="run_customers_checks",
        bash_command=(
            f"cd {PROJECT_ROOT} && {CHECK_COMMAND} "
            "--contract contracts/customers.yml "
            "--data data/samples/customers.csv"
        ),
    )

    run_orders_checks >> run_customers_checks
