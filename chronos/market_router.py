
from threading import RLock
from chronos.order_book import OrderBook


class MultiSymbolRouter:
    """Keep a separate order book for each trading symbol."""

    def __init__(self):
        self._books = {}
        self._locks = {}
        self._registry_lock = RLock()

    @staticmethod
    def _symbol(symbol):
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("Symbol must be a non-empty string")
        return symbol.strip().upper()

    def _get(self, symbol):
        symbol = self._symbol(symbol)
        with self._registry_lock:
            if symbol not in self._books:
                self._books[symbol] = OrderBook()
                self._locks[symbol] = RLock()
            return symbol, self._books[symbol], self._locks[symbol]

    def submit_order(self, symbol, order):
        _, book, lock = self._get(symbol)
        with lock:
            book.add_order(order)

    def cancel_order(self, symbol, order_id):
        _, book, lock = self._get(symbol)
        with lock:
            return book.cancel_order(order_id)

    def match(self, symbol):
        _, book, lock = self._get(symbol)
        with lock:
            book.match_orders()

    def trades(self, symbol):
        _, book, lock = self._get(symbol)
        with lock:
            return [trade.copy() for trade in book.trades]

    def statistics(self, symbol):
        _, book, lock = self._get(symbol)
        with lock:
            return book.get_statistics().copy()

    def symbols(self):
        with self._registry_lock:
            return sorted(self._books)
