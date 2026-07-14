# Architecture

## Problem

Data platforms need a repeatable way to detect contract violations before bad data reaches dashboards or ML features. Ad-hoc SQL checks in notebooks do not scale: they lack versioned contracts, historical context, or alert routing.

## Components

| Component | Responsibility |
|-----------|----------------|
| `contracts/*.yml` | Versioned schema, freshness, and FK expectations |
| `src/dqo/checks/*` | Individual validation rules |
| `src/dqo/runner.py` | Orchestrates checks into a run summary |
| `src/dqo/history.py` | Persists run and result history |
| `src/dqo/alerts.py` | Routes failures to operational channels |
| `src/dqo/cli.py` | Local and CI entry point |

## Data flow

```text
Contract YAML + CSV dataset + reference tables
              ↓
         run_checks()
              ↓
    List[CheckResult] + RunSummary
         ↙          ↘
  HistoryStore    AlertRouter
```

## Check types

1. **Schema** — dataset columns match the contract
2. **Nulls** — non-nullable columns are populated
3. **Uniqueness** — unique columns have no duplicates
4. **Freshness** — timestamps within configured max age
5. **Referential integrity** — foreign keys resolve to reference tables

## Failure modes

| Failure | Symptom | Mitigation |
|---------|---------|------------|
| Schema drift | Unexpected/missing columns | Fix upstream export or update contract via PR |
| Null violation | Required field empty | Block publish; investigate ingestion mapping |
| Duplicate keys | Uniqueness check fails | Deduplicate source or fix idempotency |
| Stale data | Freshness check fails | Verify scheduler; check upstream SLA |
| Orphan FK | Referential check fails | Repair dimension table or quarantine rows |

## Design choices

- **Contracts in YAML** — readable by engineers and analytics owners
- **SQLite default** — zero-dependency local runs and CI
- **Optional PostgreSQL** — shared history for team dashboards
- **Pluggable alert channels** — console for dev, file/webhook for ops

See [`docs/adr/0001-contract-driven-checks.md`](adr/0001-contract-driven-checks.md).
