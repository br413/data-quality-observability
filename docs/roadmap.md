# Roadmap

The product direction is a short loop: check a delivery, inspect the evidence, fix the
source, and rerun. Priorities can change with user feedback; this is not a release schedule.

## First release in this direction

- Installable `dqo` CLI with optional PostgreSQL history dependency.
- Packaged, repeatable broken-to-fixed demo.
- Offline HTML and versioned JSON reports.
- Cross-platform package smoke tests.

## Next: make failures actionable

1. **Structured row evidence.** Each check returns bounded row indices, columns, and
   reasons. Acceptance: counts remain accurate after sampling, sensitive values can
   be omitted, and HTML/JSON agree on findings.
2. **Contract validation.** Reject malformed rules with useful locations and validate
   declared types. Acceptance: unknown types and invalid booleans never silently pass.
3. **Run comparison.** Compare compatible contracts and highlight newly failing and
   resolved checks. Acceptance: version mismatches are visible and skipped checks
   never appear as fixes.

## Later, after feedback

- A browser workflow for inspecting findings and rerunning checks.
- DuckDB-backed CSV/Parquet checks with measured memory/runtime limits.
- Database dataset connectors, separate from history storage.

## Adoption work

Maintain a runnable quickstart, a current demo image, useful issue responses, and
release notes describing actual user improvements. Measure installation success,
repeat users, externally reported problems, and contributions alongside stars.
Avoid cosmetic daily commits: every change should improve behavior, evidence, or usability.
