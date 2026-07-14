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

with DAG(
    dag_id="dqo_orders_contract_checks",
    default_args=DEFAULT_ARGS,
    description="Run orders data contract checks and persist history",
    schedule="@daily",
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=["data-quality", "contracts", "portfolio"],
    doc_md="""
    ## dqo_orders_contract_checks

    1. Execute YAML contract checks against sample orders data
    2. Persist run history and route alerts to JSONL

    Set `DQO_PROJECT_ROOT` to the repository root when deploying.
    """,
) as dag:
    run_orders_checks = BashOperator(
        task_id="run_orders_checks",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            "python -m src.dqo.cli run "
            "--contract contracts/orders.yml "
            "--data data/samples/orders.csv "
            "--references data/samples "
            f"--history-db {HISTORY_DB} "
            f"--alert-file {ALERT_FILE} "
            "--no-console-alerts"
        ),
    )
