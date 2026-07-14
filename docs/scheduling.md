# Scheduling data-quality checks

## Airflow

The `dags/dqo_orders_contract_checks.py` DAG runs the orders contract daily:

```bash
export DQO_PROJECT_ROOT=/path/to/data-quality-observability
airflow dags test dqo_orders_contract_checks 2026-07-14
```

Environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `DQO_PROJECT_ROOT` | current directory | Repository root for CLI invocation |
| `DQO_DATABASE_URL` | `sqlite:///.dqo/history.db` | History store connection |
| `DQO_ALERT_FILE` | `.dqo/alerts.jsonl` | Alert JSONL destination |

## Manual / cron

For lightweight schedules without Airflow:

```bash
python -m src.dqo.cli run \
  --contract contracts/orders.yml \
  --data data/samples/orders.csv \
  --references data/samples
```

Pair with cron or a systemd timer in environments where Airflow is not deployed.
