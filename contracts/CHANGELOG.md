# Contract changelog

Version bumps follow semver policy in [ADR 0002](../docs/adr/0002-schema-registry-and-contract-versioning.md).

## orders

### 1.0 (initial)

- Columns: `order_id`, `customer_id`, `order_total`, `status`, `updated_at`
- Freshness: `updated_at` max 48 hours
- RI: `customer_id` → `customers.customer_id`

## customers

### 1.0 (initial)

- Columns: `customer_id`, `email`, `created_at`
- Uniqueness: `customer_id`, `email`
