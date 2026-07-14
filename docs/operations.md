# Operations Runbook

## Overview

| Stage | Component | Failure signal |
|-------|-----------|----------------|
| Contract load | `src.dqo.contracts` | CLI exits before checks run |
| Check execution | `src.dqo.runner` | Non-zero exit code from `cli run` |
| History | `src.dqo.history` | Missing rows in `check_runs` |
| Alerts | `src.dqo.alerts` | Entries in `.dqo/alerts.jsonl` |

## Monitoring

### What to watch

- **Latest run status:** `python -m src.dqo.cli history --contract orders`
- **Critical failures:** `[CRITICAL]` lines in console or alert file
- **Repeat failures:** same `check_type` failing across consecutive runs

### Log and alert locations

| Environment | Location |
|-------------|----------|
| Local CLI | stdout from `python -m src.dqo.cli run` |
| Alert file | `.dqo/alerts.jsonl` (configurable via `--alert-file`) |
| History DB | `.dqo/history.db` or `DQO_DATABASE_URL` |
| CI | GitHub Actions job output |

### Suggested alerts

1. Any `CRITICAL` check failure (nulls, schema, referential integrity)
2. Two consecutive `freshness` failures on the same contract
3. History store unreachable (connection error on save)

## Failure triage

### 1. Schema validation failed

**Symptoms:** `schema` check reports missing or unexpected columns.

**Steps:**

1. Compare contract `contracts/orders.yml` to upstream export
2. Confirm ETL did not rename or drop columns
3. If change is intentional, update contract in a PR with stakeholder review
4. Re-run: `python -m src.dqo.cli run --contract contracts/orders.yml --data <path> --references data/samples`

### 2. Null or uniqueness failure

**Symptoms:** `nulls` or `uniqueness` check failed.

**Steps:**

1. Inspect failing rows in source data
2. Determine if issue is upstream (source system) or mapping (transform)
3. Quarantine bad rows before publishing to consumers
4. Re-run checks after fix; confirm history shows passing run

### 3. Freshness failure

**Symptoms:** `freshness` check reports rows older than SLA.

**Steps:**

1. Verify scheduler ran on time
2. Check upstream pipeline status (see [`production-data-pipeline`](https://github.com/br413/production-data-pipeline))
3. If data is legitimately late, communicate SLA breach to stakeholders
4. Consider temporary SLA adjustment via contract PR if business agrees

### 4. Referential integrity failure

**Symptoms:** orphan foreign keys (e.g. `customer_id` not in `customers`).

**Steps:**

1. Identify orphan values from check message
2. Load reference table and confirm dimension freshness
3. Backfill dimension or remove orphan fact rows
4. Re-run with `--references` pointing at updated dimension files

### 5. Alert delivery failure

**Symptoms:** webhook channel raises `RuntimeError`.

**Steps:**

1. Verify webhook URL and network access
2. Fall back to file alerts (always enabled by default)
3. Replay alert payload from `.dqo/alerts.jsonl` if needed

## Recovery checklist

- [ ] Root cause documented in GitHub Issue
- [ ] Contract updated if schema legitimately changed
- [ ] Checks pass locally
- [ ] History shows new passing run
- [ ] Stakeholders notified if consumer-facing SLA was breached

## Escalation

| Severity | Response |
|----------|----------|
| CRITICAL | Block downstream publish; page on-call |
| WARNING (freshness) | Investigate within SLA window |
| INFO | Log only; no page |
