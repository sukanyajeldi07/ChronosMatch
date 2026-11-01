
from threading import RLock

from chronos.market_router import MultiSymbolRouter
from chronos.risk import RiskManager


class SafeMatchingEngine:
    """Route orders safely with validation and duplicate-ID protection."""

    def __init__(self, limits=None):
        self.router = MultiSymbolRouter()
        self.risk = RiskManager(limits)
        self._lock = RLock()
        self._open_ids = {}

    def submit_order(self, symbol, order):
        symbol = self.router._symbol(symbol)

        with self._lock:
            ids = self._open_ids.setdefault(symbol, set())

            if order.order_id in ids:
                raise ValueError("Duplicate open order ID")

            self.risk.validate(order, len(ids))
            self.router.submit_order(symbol, order)
            ids.add(order.order_id)

    def cancel_order(self, symbol, order_id):
        symbol = self.router._symbol(symbol)

        with self._lock:
            cancelled = self.router.cancel_order(symbol, order_id)

            if cancelled:
                self._open_ids.setdefault(symbol, set()).discard(order_id)

            return cancelled

    def match(self, symbol):
        symbol = self.router._symbol(symbol)

        with self._lock:
            self.router.match(symbol)
            _, book, lock = self.router._get(symbol)

            with lock:
                self._open_ids[symbol] = {
                    order.order_id
                    for order in book.buy_orders + book.sell_orders
                }

    def statistics(self, symbol):
        return self.router.statistics(symbol)
