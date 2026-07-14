from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.dqo.contracts import load_contract
from src.dqo.dataset import load_csv

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def orders_contract() -> object:
    return load_contract(ROOT / "contracts" / "orders.yml")


@pytest.fixture
def valid_orders() -> list[dict[str, str]]:
    return load_csv(ROOT / "data" / "samples" / "orders.csv")


@pytest.fixture
def invalid_orders() -> list[dict[str, str]]:
    return load_csv(ROOT / "data" / "samples" / "orders_invalid.csv")


@pytest.fixture
def customers() -> list[dict[str, str]]:
    return load_csv(ROOT / "data" / "samples" / "customers.csv")


@pytest.fixture
def fixed_now() -> datetime:
    return datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)
