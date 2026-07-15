# data-quality-observability

> Contract-driven data-quality checks with persisted test history and alert routing.

## Why this project exists

Downstream analytics fails quietly when schema drift, stale data, or broken foreign keys slip through ingestion. This repository demonstrates an observability layer you can run against any tabular dataset: explicit data contracts, repeatable checks, historical test results, and routed alerts for triage.

## Architecture

```text
Data contract (YAML)
    ↓
Quality check suite
    ├── schema validation
    ├── null checks
    ├── uniqueness
    ├── freshness
    └── referential integrity
    ↓
Run summary
    ├── history store (SQLite / PostgreSQL)
    └── alert router (console · file · webhook)
    ↓
On-call triage runbook
```

See [`docs/architecture.md`](docs/architecture.md) for component boundaries and failure modes.

Scheduling options are documented in [`docs/scheduling.md`](docs/scheduling.md).

## Current capabilities

- [x] YAML data contracts with column rules and foreign keys (orders, customers)
- [x] Schema validation against contract columns
- [x] Null, uniqueness, freshness, and referential-integrity checks
- [x] Check run history with SQLite (default) or PostgreSQL
- [x] Alert routing to console, JSONL file, and optional webhook
- [x] Failure triage runbook in [`docs/operations.md`](docs/operations.md)
- [x] Unit and integration tests with CI
- [x] Airflow DAG `dqo_contract_checks` for scheduled contract runs
- [ ] Webhook alert integration tests against mock server

## Technology

| Area | Selection |
|------|-----------|
| Language | Python 3.12 |
| Contracts | YAML |
| History | SQLite (local), PostgreSQL (optional) |
| Alerts | Console, JSONL file, HTTP webhook |
| Testing | pytest |
| Deployment | CLI + Docker Compose (PostgreSQL history) |

## Quick start

```bash
git clone https://github.com/br413/data-quality-observability.git
cd data-quality-observability
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
python -m src.dqo.cli run --contract contracts/orders.yml --data data/samples/orders.csv --references data/samples
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
pytest
python -m src.dqo.cli run --contract contracts/orders.yml --data data/samples/orders.csv --references data/samples
```

Run the demo script (Windows):

```powershell
.\scripts\run_demo.ps1
```

Inspect recent runs:

```bash
python -m src.dqo.cli history --contract orders
```

## Project structure

```text
.
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── workflows/ci.yml
│   └── pull_request_template.md
├── dags/
│   └── dqo_contract_checks.py
├── contracts/
│   ├── orders.yml
│   └── customers.yml
├── data/samples/
├── docs/
│   ├── architecture.md
│   ├── operations.md
│   └── adr/
├── scripts/
│   └── run_demo.ps1
├── src/dqo/
├── tests/
├── docker-compose.yml
├── README.md
├── CONTRIBUTING.md
├── SECURITY.md
└── requirements.txt
```

## Engineering decisions

Architectural Decision Records are stored in [`docs/adr/`](docs/adr/).

## Testing

```bash
pytest -v
```

Coverage includes contract loading, each check type, end-to-end runs, history persistence, and alert routing.

## Operations

| Concern | Approach |
|---------|----------|
| Scheduling | Airflow DAG `@daily` (`dqo_contract_checks`) |
| Monitoring | Check history + alert JSONL |
| Retries | Re-run after upstream fix; history preserves prior failures |
| Triage | [`docs/operations.md`](docs/operations.md) |
| Secrets | Webhook URLs via environment variables |

## Related work

Complements [`production-data-pipeline`](https://github.com/br413/production-data-pipeline), which focuses on incremental ingestion and transformation. This repository isolates the quality and observability boundary.

## Attribution

Built as a public portfolio project by [@br413](https://github.com/br413). Sample data is synthetic for demonstration.

## License

MIT — see [LICENSE](LICENSE).
