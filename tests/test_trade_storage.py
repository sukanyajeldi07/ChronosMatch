import pytest
from chronos.trade_storage import TradeStorage


def test_save_and_read_trade(tmp_path):
    storage = TradeStorage(tmp_path / "trades.db")
    trade = {
        "buy_order_id": "B1",
        "sell_order_id": "S1",
        "price": 100,
        "quantity": 3,
    }
    storage.save_trade("AAPL", trade)
    saved = storage.get_trades("AAPL")
    assert len(saved) == 1
    assert saved[0]["quantity"] == 3
    assert saved[0]["price"] == 100


def test_trade_survives_reopening(tmp_path):
    db_path = tmp_path / "trades.db"
    storage = TradeStorage(db_path)
    storage.save_trade("MSFT", {
        "buy_order_id": "B2",
        "sell_order_id": "S2",
        "price": 200,
        "quantity": 2,
    })
    reopened = TradeStorage(db_path)
    assert len(reopened.get_trades("MSFT")) == 1


def test_invalid_trade_is_rejected(tmp_path):
    storage = TradeStorage(tmp_path / "trades.db")
    with pytest.raises(ValueError):
        storage.save_trade("AAPL", {
            "buy_order_id": "B1",
            "sell_order_id": "S1",
            "price": -1,
            "quantity": 3,
        })
