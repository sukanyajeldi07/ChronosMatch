
import pytest

from chronos.order_book import Order, OrderBook
from chronos.market_router import MultiSymbolRouter
from chronos.risk import RiskManager, RiskLimits
from chronos.safe_engine import SafeMatchingEngine


def test_order_book_cancels_pending_order():
    book = OrderBook()
    book.add_order(Order("B1", "BUY", 100, 5))

    assert book.cancel_order("B1") is True
    assert book.cancel_order("B1") is False


def test_trade_summary_after_matching():
    book = OrderBook()
    book.add_order(Order("B1", "BUY", 105, 4))
    book.add_order(Order("S1", "SELL", 100, 3))
    book.match_orders()

    summary = book.get_trade_summary()
    assert summary["total_trades"] == 1
    assert summary["total_traded_quantity"] == 3


def test_router_keeps_symbols_separate():
    router = MultiSymbolRouter()
    router.submit_order("AAPL", Order("A1", "BUY", 100, 2))
    router.submit_order("MSFT", Order("M1", "BUY", 200, 3))

    assert router.symbols() == ["AAPL", "MSFT"]
    assert router.cancel_order("AAPL", "A1") is True
    assert router.cancel_order("MSFT", "M1") is True


def test_risk_manager_rejects_excessive_quantity():
    risk = RiskManager(RiskLimits(max_order_quantity=10))

    with pytest.raises(ValueError):
        risk.validate(Order("B1", "BUY", 100, 11))


def test_safe_engine_rejects_duplicate_open_order_id():
    engine = SafeMatchingEngine()
    engine.submit_order("AAPL", Order("A1", "BUY", 100, 2))

    with pytest.raises(ValueError, match="Duplicate"):
        engine.submit_order("AAPL", Order("A1", "BUY", 99, 1))


def test_safe_engine_routes_and_matches_orders():
    engine = SafeMatchingEngine()
    engine.submit_order("AAPL", Order("B1", "BUY", 105, 3))
    engine.submit_order("AAPL", Order("S1", "SELL", 100, 2))
    engine.match("AAPL")

    trades = engine.router.trades("AAPL")
    assert len(trades) == 1
    assert trades[0]["quantity"] == 2
    assert engine.router.trades("MSFT") == []
