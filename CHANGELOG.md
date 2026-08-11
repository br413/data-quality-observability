# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Added

- Webhook alert integration tests for `WebhookAlertChannel` and router fan-out

## [0.1.0] - 2026-07-14

### Added

- YAML data contracts with column, freshness, and referential-integrity rules
- Quality check suite: schema, nulls, uniqueness, freshness, referential integrity
- CLI for running checks and viewing history
- SQLite and PostgreSQL history stores
- Alert routing to console, JSONL file, and webhook
- Operations runbook and architecture documentation
- pytest suite and GitHub Actions CI
