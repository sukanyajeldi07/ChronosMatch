
import pytest

from chronos.order_book import Order, OrderBook
from chronos.matching_engine import MatchingEngine


def test_matching_engine():
    engine = MatchingEngine()

    buy_order = Order(1, "BUY", 110, 5)
    sell_order = Order(2, "SELL", 105, 5)

    engine.submit_order(buy_order)
    engine.submit_order(sell_order)
    engine.execute()

    assert len(engine.order_book.trades) == 1


def test_matching_engine_does_not_match_when_prices_do_not_cross():
    engine = MatchingEngine()

    buy_order = Order(3, "BUY", 100, 5)
    sell_order = Order(4, "SELL", 105, 5)

    engine.submit_order(buy_order)
    engine.submit_order(sell_order)
    engine.execute()

    assert len(engine.order_book.trades) == 0


def test_matching_engine_with_different_quantities():
    engine = MatchingEngine()

    buy_order = Order(5, "BUY", 110, 10)
    sell_order = Order(6, "SELL", 105, 5)

    engine.submit_order(buy_order)
    engine.submit_order(sell_order)
    engine.execute()

    assert len(engine.order_book.trades) == 1
    assert engine.order_book.trades[0]["quantity"] == 5
    assert buy_order.quantity == 5


def test_partial_fill_keeps_remaining_buy_quantity():
    engine = MatchingEngine()

    buy_order = Order(7, "BUY", 110, 10)
    sell_order = Order(8, "SELL", 105, 4)

    engine.submit_order(buy_order)
    engine.submit_order(sell_order)
    engine.execute()

    assert len(engine.order_book.trades) == 1
    assert engine.order_book.trades[0]["quantity"] == 4
    assert buy_order.quantity == 6
    assert len(engine.order_book.buy_orders) == 1
    assert len(engine.order_book.sell_orders) == 0


def test_order_rejects_zero_quantity():
    with pytest.raises(ValueError):
        Order(9, "BUY", 100, 0)


@pytest.mark.parametrize(
    "order_id, side, price, quantity",
    [
        (10, "BUY", 0, 5),
        (11, "SELL", -1, 5),
        (12, "INVALID", 100, 5),
        (13, "BUY", 100, 0),
        (14, "SELL", 100, -2),
    ],
)
def test_invalid_orders_are_rejected(order_id, side, price, quantity):
    with pytest.raises(ValueError):
        Order(order_id, side, price, quantity)


def test_multiple_orders_create_expected_trades():
    engine = MatchingEngine()

    buy_order_1 = Order(20, "BUY", 110, 5)
    buy_order_2 = Order(21, "BUY", 105, 3)
    sell_order_1 = Order(22, "SELL", 100, 4)
    sell_order_2 = Order(23, "SELL", 105, 4)

    engine.submit_order(buy_order_1)
    engine.submit_order(buy_order_2)
    engine.submit_order(sell_order_1)
    engine.submit_order(sell_order_2)

    engine.execute()

    assert len(engine.order_book.trades) == 3
    assert sum(
        trade["quantity"] for trade in engine.order_book.trades
    ) == 8


def test_higher_buy_price_is_matched_first():
    engine = MatchingEngine()

    lower_buy = Order(30, "BUY", 100, 5)
    higher_buy = Order(31, "BUY", 110, 5)
    sell = Order(32, "SELL", 100, 5)

    engine.submit_order(lower_buy)
    engine.submit_order(higher_buy)
    engine.submit_order(sell)

    engine.execute()

    assert len(engine.order_book.trades) == 1
    assert engine.order_book.trades[0]["buy_order_id"] == 31
    assert engine.order_book.trades[0]["quantity"] == 5
    assert lower_buy.quantity == 5
    assert higher_buy.quantity == 0


def test_lower_sell_price_is_matched_first():
    engine = MatchingEngine()

    buy_order = Order(40, "BUY", 120, 5)
    higher_sell = Order(41, "SELL", 110, 5)
    lower_sell = Order(42, "SELL", 100, 5)

    engine.submit_order(buy_order)
    engine.submit_order(higher_sell)
    engine.submit_order(lower_sell)

    engine.execute()

    assert len(engine.order_book.trades) == 1
    assert engine.order_book.trades[0]["sell_order_id"] == 42
    assert engine.order_book.trades[0]["price"] == 100
    assert engine.order_book.trades[0]["quantity"] == 5
    assert higher_sell.quantity == 5
    assert lower_sell.quantity == 0


def test_same_price_buy_orders_follow_fifo():
    engine = MatchingEngine()

    first_buy = Order(50, "BUY", 100, 5)
    second_buy = Order(51, "BUY", 100, 5)
    sell = Order(52, "SELL", 100, 5)

    engine.submit_order(first_buy)
    engine.submit_order(second_buy)
    engine.submit_order(sell)

    engine.execute()

    assert len(engine.order_book.trades) == 1
    assert engine.order_book.trades[0]["buy_order_id"] == 50
    assert first_buy.quantity == 0
    assert second_buy.quantity == 5


def test_order_book_statistics_with_pending_orders():
    book = OrderBook()

    book.add_order(Order(60, "BUY", 110, 10))
    book.add_order(Order(61, "SELL", 115, 4))

    stats = book.get_statistics()

    assert stats["pending_buy_orders"] == 1
    assert stats["pending_sell_orders"] == 1
    assert stats["pending_buy_quantity"] == 10
    assert stats["pending_sell_quantity"] == 4
    assert stats["total_trades"] == 0
    assert stats["total_traded_quantity"] == 0


def test_order_book_statistics_after_trades():
    book = OrderBook()

    book.add_order(Order(70, "BUY", 110, 10))
    book.add_order(Order(71, "SELL", 108, 6))

    book.match_orders()
    stats = book.get_statistics()

    assert stats["pending_buy_orders"] == 1
    assert stats["pending_sell_orders"] == 0
    assert stats["pending_buy_quantity"] == 4
    assert stats["pending_sell_quantity"] == 0
    assert stats["total_trades"] == 1
    assert stats["total_traded_quantity"] == 6


def test_trade_summary_after_trades():
    book = OrderBook()

    book.add_order(Order(80, "BUY", 110, 10))
    book.add_order(Order(81, "SELL", 108, 8))
    book.add_order(Order(82, "SELL", 109, 6))

    book.match_orders()

    summary = book.get_trade_summary()

    assert summary["total_trades"] == 2
    assert summary["total_traded_quantity"] == 10
    assert summary["average_trade_price"] == 108.2
    assert summary["highest_trade_price"] == 109
    assert summary["lowest_trade_price"] == 108


def test_trade_summary_without_trades():
    book = OrderBook()

    summary = book.get_trade_summary()

    assert summary["total_trades"] == 0
    assert summary["total_traded_quantity"] == 0
    assert summary["average_trade_price"] == 0
    assert summary["highest_trade_price"] == 0
    assert summary["lowest_trade_price"] == 0

def test_cancel_pending_buy_order():
    book = OrderBook()
    order = Order(90, "BUY", 100, 5)
    book.add_order(order)

    result = book.cancel_order(90)

    assert result is True
    assert len(book.buy_orders) == 0


def test_cancel_nonexistent_order():
    book = OrderBook()

    result = book.cancel_order(999)

    assert result is False
def test_cancel_pending_sell_order():
    book = OrderBook()
    order = Order(91, "SELL", 110, 5)
    book.add_order(order)

    result = book.cancel_order(91)

    assert result is True
    assert len(book.sell_orders) == 0


def test_cancel_filled_order_returns_false():
    book = OrderBook()
    buy_order = Order(92, "BUY", 110, 5)
    sell_order = Order(93, "SELL", 105, 5)

    book.add_order(buy_order)
    book.add_order(sell_order)
    book.match_orders()

    result = book.cancel_order(92)

    assert result is False
def test_matching_engine_displays_statistics():
    engine = MatchingEngine()

    engine.submit_order(Order(101, "BUY", 110, 5))
    engine.submit_order(Order(102, "SELL", 115, 3))

    stats = engine.order_book.get_statistics()

    assert stats["pending_buy_orders"] == 1
    assert stats["pending_sell_orders"] == 1
    assert stats["total_trades"] == 0


def test_matching_engine_executes_multiple_trades():
    engine = MatchingEngine()

    engine.submit_order(Order(103, "BUY", 110, 5))
    engine.submit_order(Order(104, "SELL", 105, 2))
    engine.submit_order(Order(105, "SELL", 108, 3))

    engine.execute()

    assert len(engine.order_book.trades) == 2
    assert sum(
        trade["quantity"] for trade in engine.order_book.trades
    ) == 5
    assert len(engine.order_book.buy_orders) == 0
    assert len(engine.order_book.sell_orders) == 0
