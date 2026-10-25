
class Order:

    def __init__(self, order_id, side, price, quantity):
        self.order_id = order_id
        self.side = side
        self.price = price
        self.quantity = quantity


class OrderBook:

    def __init__(self):
        self.buy_orders = []
        self.sell_orders = []
        self.trades = []

    def add_order(self, order):

        if order.side == "BUY":
            self.buy_orders.append(order)

            self.buy_orders.sort(
                key=lambda order: order.price,
                reverse=True
            )

        elif order.side == "SELL":
            self.sell_orders.append(order)

            self.sell_orders.sort(
                key=lambda order: order.price
            )

        else:
            print("Invalid order side")

    def match_orders(self):

        while self.buy_orders and self.sell_orders:

            buy_order = self.buy_orders[0]
            sell_order = self.sell_orders[0]

            if buy_order.price >= sell_order.price:

                trade_quantity = min(
                    buy_order.quantity,
                    sell_order.quantity
                )

                trade_price = sell_order.price

                trade = {
                    "buy_order_id": buy_order.order_id,
                    "sell_order_id": sell_order.order_id,
                    "price": trade_price,
                    "quantity": trade_quantity
                }

                self.trades.append(trade)

                print("\nTrade Executed")
                print("Price:", trade_price)
                print("Quantity:", trade_quantity)

                buy_order.quantity -= trade_quantity
                sell_order.quantity -= trade_quantity

                if buy_order.quantity == 0:
                    self.buy_orders.pop(0)

                if sell_order.quantity == 0:
                    self.sell_orders.pop(0)

            else:
                break

    def display(self):

        print("\nBUY ORDERS")

        for order in self.buy_orders:
            print(
                order.order_id,
                order.price,
                order.quantity
            )

        print("\nSELL ORDERS")

        for order in self.sell_orders:
            print(
                order.order_id,
                order.price,
                order.quantity
            )

    def display_trades(self):

        print("\nCOMPLETED TRADES")

        for trade in self.trades:
            print(
                "BUY:", trade["buy_order_id"],
                "SELL:", trade["sell_order_id"],
                "PRICE:", trade["price"],
                "QUANTITY:", trade["quantity"]
            )


if __name__ == "__main__":

    book = OrderBook()

    order1 = Order(1, "BUY", 100, 10)
    order2 = Order(2, "BUY", 105, 5)

    order3 = Order(3, "SELL", 110, 8)
    order4 = Order(4, "SELL", 108, 6)

    book.add_order(order1)
    book.add_order(order2)
    book.add_order(order3)
    book.add_order(order4)

    book.display()

    book.match_orders()

    book.display()

    book.display_trades()
