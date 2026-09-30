# Contributing

## Development setup

Use Python 3.10+ in a virtual environment:

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python scripts/validate_registry.py
dqo demo --output my-demo
```

Airflow tests skip when it is not installed. The integration CI job runs them on
Linux with PostgreSQL; neither service is needed for CLI, report, or check work.
The installed package imports as `dqo`; checkout-based `src.dqo` imports remain compatible.

## Good starting points

- Add a small, anonymized CSV fixture and regression test for a check bug.
- Improve report accessibility or explain an ambiguous finding.
- Try installation on your operating system and report missing steps.

For a new check, describe null/empty-input behavior and the evidence returned on
failure. See [the roadmap](docs/roadmap.md) for planned features and acceptance criteria.
Never commit customer data, credentials, or generated history databases.

## Workflow

1. Open or select an issue.
2. Discuss significant design changes before implementation.
3. Create a focused branch.
4. Add or update tests.
5. Run all quality checks locally.
6. Open a pull request with technical context and validation evidence.

## Commit guidance

Use concise, meaningful messages:

```text
feat: add freshness check against contract
fix: handle empty reference tables
test: cover alert routing for critical failures
docs: document failure triage procedure
```

Preserve accurate authorship. Use co-authorship only when both parties genuinely contributed.

## Pull-request standard

A pull request should explain:

- Problem
- Approach
- Alternatives considered
- Testing performed
- Operational impact
- Rollback strategy, when relevant
