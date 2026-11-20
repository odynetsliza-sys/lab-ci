from unittest.mock import Mock

import pytest

from shop.cart import Cart
from tests.conftest import FakeRates


# --- Базова поведінка ---
def test_new_cart_is_empty(cart: Cart) -> None:
    assert cart.items_count() == 0
    assert cart.total() == 0


def test_add_item_with_qty(cart: Cart) -> None:
    cart.add("book", price=200.0, qty=2)
    assert cart.items_count() == 2
    assert cart.total() == 400.0


def test_add_item_default_qty_is_one(cart: Cart) -> None:
    cart.add("pen", price=15.0)
    assert cart.items_count() == 1


def test_add_same_name_increases_qty(cart: Cart) -> None:
    cart.add("book", price=200.0)
    cart.add("book", price=200.0, qty=2)
    assert cart.items_count() == 3
    assert cart.total() == 600.0


def test_add_same_name_different_price_keeps_first_price(cart: Cart) -> None:
    # Рішення: ціна береться з першого додавання, повторне додавання міняє лише кількість.
    cart.add("book", price=200.0)
    cart.add("book", price=300.0)
    assert cart.items_count() == 2
    assert cart.total() == 400.0


def test_items_count_with_fixture(cart_with_items: Cart) -> None:
    assert cart_with_items.items_count() == 6


def test_total_with_fixture(cart_with_items: Cart) -> None:
    assert cart_with_items.total() == pytest.approx(460.0)


def test_total_rounding_uses_approx(cart: Cart) -> None:
    cart.add("x", price=0.1, qty=3)
    assert cart.total() == pytest.approx(0.3)


def test_remove_item(cart_with_items: Cart) -> None:
    cart_with_items.remove("pen")
    assert cart_with_items.items_count() == 2
    assert cart_with_items.total() == 400.0


# --- Параметризація: граничні значення знижки ---
@pytest.mark.parametrize(
    ("discount", "expected"),
    [(0, 400.0), (10, 360.0), (50, 200.0), (100, 0.0)],
)
def test_discounts(cart: Cart, discount: int, expected: float) -> None:
    cart.add("book", price=200.0, qty=2)
   assert cart.total(discount_percent=discount) == expected + 10


# --- Винятки ---
def test_add_negative_price_raises(cart: Cart) -> None:
    with pytest.raises(ValueError, match="price"):
        cart.add("book", price=-1.0)


@pytest.mark.parametrize("qty", [0, -1])
def test_add_non_positive_qty_raises(cart: Cart, qty: int) -> None:
    with pytest.raises(ValueError, match="qty"):
        cart.add("book", price=10.0, qty=qty)


def test_remove_missing_item_raises(cart: Cart) -> None:
    with pytest.raises(KeyError):
        cart.remove("ghost")


@pytest.mark.parametrize("discount", [-1, 101])
def test_invalid_discount_raises(cart: Cart, discount: float) -> None:
    with pytest.raises(ValueError, match="discount_percent"):
        cart.total(discount_percent=discount)


@pytest.mark.parametrize("rate", [0.0, -5.0])
def test_total_in_invalid_rate_raises(cart: Cart, rate: float) -> None:
    with pytest.raises(ValueError, match="rate"):
        cart.total_in("USD", FakeRates(rate))


# --- Тестові дублери ---
def test_total_in_usd_with_mock() -> None:
    rates = Mock()
    rates.get_rate.return_value = 40.0  # 1 USD = 40 UAH
    cart = Cart()
    cart.add("book", price=400.0)
    assert cart.total_in("USD", rates) == 10.0
    rates.get_rate.assert_called_once_with("USD")


def test_total_in_with_fake_rates(cart_with_items: Cart) -> None:
    assert cart_with_items.total_in("EUR", FakeRates(46.0)) == 10.0  # 460 / 46