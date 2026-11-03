
import sqlite3
from pathlib import Path


class TradeStorage:
    def __init__(self, db_path="data/trades.db"):
        self.db_path = str(db_path)

        Path(self.db_path).parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with sqlite3.connect(self.db_path) as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    buy_order_id TEXT NOT NULL,
                    sell_order_id TEXT NOT NULL,
                    price REAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def save_trade(self, symbol, trade):
        required_fields = (
            "buy_order_id",
            "sell_order_id",
            "price",
            "quantity",
        )

        if not symbol:
            raise ValueError("Symbol is required")

        if not isinstance(trade, dict):
            raise ValueError("Trade must be a dictionary")

        if any(field not in trade for field in required_fields):
            raise ValueError("Missing trade fields")

        try:
            price = float(trade["price"])
            quantity = int(trade["quantity"])
        except (TypeError, ValueError):
            raise ValueError("Price and quantity must be valid numbers")

        if price <= 0 or quantity <= 0:
            raise ValueError("Price and quantity must be positive")

        with sqlite3.connect(self.db_path) as connection:
            connection.execute("""
                INSERT INTO trades (
                    symbol,
                    buy_order_id,
                    sell_order_id,
                    price,
                    quantity
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                symbol,
                trade["buy_order_id"],
                trade["sell_order_id"],
                price,
                quantity,
            ))

    def get_trades(self, symbol=None):
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row

            if symbol:
                rows = connection.execute(
                    """
                    SELECT * FROM trades
                    WHERE symbol = ?
                    ORDER BY id
                    """,
                    (symbol,),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM trades ORDER BY id"
                ).fetchall()

            return [dict(row) for row in rows]
