# ADR 0001: Contract-driven quality checks

## Status

Accepted

## Context

Quality rules scattered across SQL scripts and notebooks are hard to review, version, and alert on. We need a single source of truth that engineers and analytics stakeholders can inspect.

## Decision

Define data expectations in version-controlled YAML contracts. Map each contract to a composable check suite that produces structured results, persists history, and routes alerts.

## Consequences

**Positive**

- Contracts are reviewable in pull requests
- Checks are testable without a live warehouse
- History enables trend analysis and repeat-failure detection

**Negative**

- Contracts must be maintained when schemas change
- YAML contracts do not replace column-level type enforcement in the warehouse

## Alternatives considered

- **dbt tests only** — excellent for warehouse-native checks but less portable for pre-load validation
- **Great Expectations** — heavier dependency; this portfolio project prioritizes a small, readable codebase
