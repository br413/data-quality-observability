from pathlib import Path

from src.dqo.contracts import load_contract


def test_load_orders_contract() -> None:
    contract = load_contract(Path("contracts/orders.yml"))
    assert contract.name == "orders"
    assert contract.version == "1.0"
    assert contract.freshness is not None
    assert contract.freshness.column == "updated_at"
    assert len(contract.foreign_keys) == 1


def test_load_customers_contract() -> None:
    contract = load_contract(Path("contracts/customers.yml"))
    assert contract.name == "customers"
    assert contract.freshness is None
    assert {column.name for column in contract.columns} == {
        "customer_id",
        "full_name",
        "region",
    }
    customer_id_column = next(column for column in contract.columns if column.name == "customer_id")
    assert customer_id_column.unique is True
