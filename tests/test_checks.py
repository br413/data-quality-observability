from src.dqo.checks.freshness import validate_freshness
from src.dqo.checks.nulls import validate_nulls
from src.dqo.checks.referential import validate_referential_integrity
from src.dqo.checks.schema import validate_schema
from src.dqo.checks.uniqueness import validate_uniqueness
from src.dqo.models import CheckStatus


def test_schema_passes_for_valid_orders(orders_contract, valid_orders) -> None:
    result = validate_schema(orders_contract, valid_orders)
    assert result.status == CheckStatus.PASSED


def test_nulls_fail_for_missing_total(orders_contract, invalid_orders) -> None:
    result = validate_nulls(orders_contract, invalid_orders)
    assert result.status == CheckStatus.FAILED
    assert "order_total" in result.message


def test_uniqueness_fails_for_duplicate_order_id(orders_contract, invalid_orders) -> None:
    result = validate_uniqueness(orders_contract, invalid_orders)
    assert result.status == CheckStatus.FAILED
    assert "order_id" in result.message


def test_freshness_fails_for_stale_rows(orders_contract, invalid_orders, fixed_now) -> None:
    result = validate_freshness(orders_contract, invalid_orders, now=fixed_now)
    assert result.status == CheckStatus.FAILED


def test_referential_integrity_fails_for_orphans(
    orders_contract,
    invalid_orders,
    customers,
) -> None:
    result = validate_referential_integrity(
        orders_contract,
        invalid_orders,
        {"customers": customers},
    )
    assert result.status == CheckStatus.FAILED
    assert "C999" in result.message
