# ADR 0002: Schema registry and contract versioning (design)

## Status

Proposed — design accepted; implementation tracked for a future release

## Context

[ADR 0001](0001-contract-driven-checks.md) established YAML contracts as the quality boundary. Each contract already carries a `version` field (e.g. `orders.yml` → `"1.0"`), but today:

- **No registry** — consumers must know the file path; there is no canonical index of datasets and active versions
- **No compatibility rules** — adding a required column or tightening a freshness window is indistinguishable from a safe docs edit in review
- **No run attribution** — history stores check outcomes but not which contract version was evaluated
- **No cross-repo pin** — [production-data-pipeline](https://github.com/br413/production-data-pipeline) quarantine handles row-level failures; dataset contracts in this repo are not yet referenced by name/version from ingestion configs

Production teams solve this with schema registries (Confluent, AWS Glue Schema Registry, Data Contract CLI ecosystems). This portfolio project needs a **lightweight, git-native** design that demonstrates senior platform thinking without operating a separate registry service.

## Decision

Introduce a **file-based contract registry** and **semver versioning policy** before any HTTP registry or warehouse integration.

### 1. Registry index

Add `contracts/registry.yml` as the canonical catalog:

```yaml
contracts:
  orders:
    current: "1.0"
    path: orders.yml
    owners: [data-platform]
  customers:
    current: "1.0"
    path: customers.yml
    owners: [data-platform]
```

The CLI resolves `--contract orders` to `registry.yml → orders.yml` instead of requiring a file path. `current` is the default version pin for scheduled runs and CI.

### 2. Versioning policy (semver)

| Change type | Version bump | Example |
|-------------|--------------|---------|
| Add optional column | PATCH (`1.0` → `1.0.1`) | New nullable `discount_code` |
| Tighten freshness / add optional check | MINOR (`1.0` → `1.1`) | `max_age_hours: 48 → 24` with grace period documented |
| Add required column, remove column, rename | MAJOR (`1.0` → `2.0`) | `order_total` becomes required |
| Referential integrity change | MAJOR | New FK to a new dimension |

Breaking changes require:

1. Major version bump in contract YAML
2. `registry.yml` `current` update in the **same PR** as the contract change
3. Entry in `contracts/CHANGELOG.md` (new file) describing consumer impact

### 3. Run history attribution

Extend `RunSummary` metadata (future implementation) with:

- `contract_name`
- `contract_version`
- `registry_revision` (git SHA or optional content hash of registry + contract file)

This makes quality regressions auditable: “orders failed freshness on **v1.1** starting 2026-08-12.”

### 4. Compatibility with ingestion quarantine

Registry design keeps **row-level** and **dataset-level** gates separate:

| Boundary | Project | Responsibility |
|----------|---------|----------------|
| Row-level poison pills | `production-data-pipeline` | Quarantine during API ingestion ([ADR 0004](https://github.com/br413/production-data-pipeline/blob/main/docs/adr/0004-failed-record-quarantine.md)) |
| Dataset contract | `data-quality-observability` | Schema, freshness, RI after landing / before promote |

Future optional integration: pipeline config pins `quality_contract: orders@1.0` and exports landed CSV/Parquet for `dqo.cli run --contract orders --version 1.0`. Not required for registry v1.

### 5. CI enforcement (future)

When implemented:

- `pytest` loads registry and validates every `path` exists
- PR check fails if contract `version` changes without registry or CHANGELOG update
- `validate --strict` mode rejects datasets that do not match `current` pin

## Consequences

**Positive**

- Contracts become discoverable and pin-able by name/version
- Breaking changes are explicit in review, not silent schema drift
- History can answer “which contract version failed?” — critical for on-call
- Design scales to a real registry service later without rewriting contracts

**Negative**

- Extra files to maintain (`registry.yml`, `CHANGELOG.md`)
- Semver discipline adds friction for solo devs — acceptable for portfolio signal
- Full cross-repo pinning with `production-data-pipeline` is follow-on work

## Alternatives considered

| Alternative | Why not (for this portfolio) |
|-------------|--------------------------------|
| **Confluent Schema Registry** | Heavy ops; Avro/Protobuf focus; obscures readable YAML contract story |
| **dbt exposures / metrics only** | Warehouse-native; does not cover pre-load CSV/API validation |
| **Version field only, no registry** | Current state — does not scale past two contracts |
| **Git tags as versions** | Poor discoverability; hard to pin in Airflow/CLI |

## Implementation phases

| Phase | Scope | Deliverable |
|-------|-------|-------------|
| **1** | Registry + docs | `contracts/registry.yml`, ADR 0002, README update |
| **2** | CLI resolution | `--contract orders` resolves via registry; `--version` override |
| **3** | History metadata | Persist `contract_version` in run history | ✓ |
| **4** | CI guards | Registry consistency tests; CHANGELOG requirement |
| **5** | Pipeline pin (optional) | Config reference from `production-data-pipeline` |

Phases 1–2 are the minimum viable registry story for portfolio reviewers.

## References

- [Data Quality Contracts in Production Pipelines (Dev.to)](https://dev.to/bobby_ray_581732c715283b2/data-quality-contracts-in-production-pipelines-without-a-separate-platform-team-f3)
- [production-data-pipeline ADR 0004 — quarantine](https://github.com/br413/production-data-pipeline/blob/main/docs/adr/0004-failed-record-quarantine.md)
- [architecture.md](../architecture.md)
