from pathlib import Path

from src.dqo.contracts import load_contract


def test_load_orders_contract() -> None:
    contract = load_contract(Path("contracts/orders.yml"))
    assert contract.name == "orders"
    assert contract.version == "1.0"
    assert contract.freshness is not None
    assert contract.freshness.column == "updated_at"
    assert len(contract.foreign_keys) == 1
