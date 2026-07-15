"""Validate Airflow DAG integrity."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("airflow")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DAGS_FOLDER = str(PROJECT_ROOT / "dags")

sys.path.insert(0, DAGS_FOLDER)
os.environ.setdefault("AIRFLOW_HOME", str(PROJECT_ROOT / ".airflow"))


def test_dag_loads_without_import_errors() -> None:
    from airflow.models import DagBag

    dag_bag = DagBag(dag_folder=DAGS_FOLDER, include_examples=False)
    assert dag_bag.import_errors == {}, f"DAG import errors: {dag_bag.import_errors}"

    dag = dag_bag.get_dag("dqo_contract_checks")
    assert dag is not None
    assert len(dag.tasks) == 2


def test_dag_schedule_and_tags() -> None:
    from airflow.models import DagBag

    dag_bag = DagBag(dag_folder=DAGS_FOLDER, include_examples=False)
    dag = dag_bag.get_dag("dqo_contract_checks")
    assert dag is not None
    assert dag.schedule_interval == "@daily"
    assert "data-quality" in dag.tags
