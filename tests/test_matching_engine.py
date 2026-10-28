
from chronos.order_book import Order
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
