
from chronos.order_book import Order, OrderBook


class MatchingEngine:

    def __init__(self):
        self.order_book = OrderBook()

    def submit_order(self, order):
        self.order_book.add_order(order)

    def execute(self):
        self.order_book.match_orders()

    def display_orders(self):
        self.order_book.display()

    def display_trades(self):
        self.order_book.display_trades()


if __name__ == "__main__":

    engine = MatchingEngine()

    order1 = Order(1, "BUY", 100, 10)
    order2 = Order(2, "BUY", 110, 5)
    order3 = Order(3, "SELL", 105, 8)
    order4 = Order(4, "SELL", 115, 6)

    engine.submit_order(order1)
    engine.submit_order(order2)
    engine.submit_order(order3)
    engine.submit_order(order4)

    print("\nORDER BOOK")
    engine.display_orders()

    print("\nMATCHING ORDERS")
    engine.execute()

    print("\nCOMPLETED TRADES")
    engine.display_trades()

    print("\nREMAINING ORDERS")
    engine.display_orders()
