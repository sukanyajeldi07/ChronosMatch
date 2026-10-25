
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
