
from chronos.order_book import Order, OrderBook


class MatchingEngine:
    def __init__(self):
        self.order_book = OrderBook()

    def submit_order(self, order):
        self.order_book.add_order(order)

    def execute(self):
        self.order_book.match_orders()

    def cancel_order(self, order_id):
        return self.order_book.cancel_order(order_id)

    def get_best_bid(self):
        return self.order_book.get_best_bid()

    def get_best_ask(self):
        return self.order_book.get_best_ask()

    def get_bid_ask_spread(self):
        return self.order_book.get_bid_ask_spread()

    def get_statistics(self):
        return self.order_book.get_statistics()

    def get_trade_summary(self):
        return self.order_book.get_trade_summary()

    def get_trade_history(self):
        return self.order_book.get_trade_history()

    def get_execution_metrics(self):
        return self.order_book.get_execution_metrics()

    def display_orders(self):
        self.order_book.display()

    def display_trades(self):
        self.order_book.display_trades()


if __name__ == "__main__":
    engine = MatchingEngine()

    engine.submit_order(Order(1, "BUY", 110, 10))
    engine.submit_order(Order(2, "BUY", 105, 5))
    engine.submit_order(Order(3, "SELL", 108, 8))
    engine.submit_order(Order(4, "SELL", 109, 6))

    print("BEST BID:", engine.get_best_bid())
    print("BEST ASK:", engine.get_best_ask())
    print("SPREAD:", engine.get_bid_ask_spread())

    engine.execute()

    print("\nTRADE HISTORY")
    print(engine.get_trade_history())

    print("\nEXECUTION METRICS")
    print(engine.get_execution_metrics())

    print("\nSTATISTICS")
    print(engine.get_statistics())
