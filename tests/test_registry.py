from pathlib import Path

import pytest

from src.dqo.registry import load_registry, resolve_contract_path


def test_load_registry_lists_orders_and_customers() -> None:
    registry = load_registry(Path("contracts/registry.yml"))
    assert set(registry) == {"orders", "customers"}
    assert registry["orders"]["current"] == "1.0"


def test_resolve_contract_by_registry_name() -> None:
    path = resolve_contract_path("orders")
    assert path == Path("contracts/orders.yml")


def test_resolve_contract_by_relative_yml_path() -> None:
    path = resolve_contract_path("contracts/orders.yml")
    assert path == Path("contracts/orders.yml")


def test_resolve_unknown_contract_raises() -> None:
    with pytest.raises(ValueError, match="Unknown contract 'missing'"):
        resolve_contract_path("missing")
