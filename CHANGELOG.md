# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Added

- Installable `dqo` command with optional PostgreSQL dependencies.
- `dqo demo`: bundled broken/fixed fixtures, SQLite history, and offline HTML/JSON reports.
- `dqo run --report` with escaped HTML output and versioned JSON exports.
- Package CI for Windows/Linux and Python 3.10/3.12, including wheel installation outside the checkout.
- User-focused quickstart, demo preview, contributor entry points, and roadmap.
- Webhook alert integration tests for `WebhookAlertChannel` and router fan-out

### Fixed

- Schema mismatches now skip dependent checks instead of raising missing-column errors.
- Invalid freshness timestamps produce failed findings instead of aborting a run.
- Explicit `.yaml` and `.yml` paths are supported; missing paths do not fall back to an unrelated file.

## [0.1.0] - 2026-07-14

### Added

- YAML data contracts with column, freshness, and referential-integrity rules
- Quality check suite: schema, nulls, uniqueness, freshness, referential integrity
- CLI for running checks and viewing history
- SQLite and PostgreSQL history stores
- Alert routing to console, JSONL file, and webhook
- Operations runbook and architecture documentation
- pytest suite and GitHub Actions CI
