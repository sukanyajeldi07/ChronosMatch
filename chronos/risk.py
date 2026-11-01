
from dataclasses import dataclass


@dataclass
class RiskLimits:
    max_order_quantity: int = 10000
    min_price: float = 0.01
    max_price: float = 1_000_000.0


class RiskManager:
    """Validate orders before they enter the order book."""

    def __init__(self, limits=None):
        self.limits = limits or RiskLimits()

    def validate(self, order, current_open_orders=0):
        if not hasattr(order, "order_id"):
            raise ValueError("Invalid order")

        if order.side not in ("BUY", "SELL"):
            raise ValueError("Invalid order side")

        if not isinstance(order.quantity, int) or isinstance(order.quantity, bool):
            raise ValueError("Invalid order quantity")

        if not 0 < order.quantity <= self.limits.max_order_quantity:
            raise ValueError("Order quantity exceeds risk limits")

        if not isinstance(order.price, (int, float)) or isinstance(order.price, bool):
            raise ValueError("Invalid order price")

        if not self.limits.min_price <= order.price <= self.limits.max_price:
            raise ValueError("Order price outside risk limits")

        return True
