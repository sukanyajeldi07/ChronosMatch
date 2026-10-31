
class Order:
    def __init__(self, order_id, side, price, quantity):
        if side not in ("BUY", "SELL"):
            raise ValueError("Side must be BUY or SELL")

        if price <= 0:
            raise ValueError("Price must be greater than zero")

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")

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
        if not isinstance(order, Order):
            raise TypeError("Order must be an Order object")

        # Validate the order side even if it changes after creation.
        if order.side not in ("BUY", "SELL"):
            raise ValueError("Order side must be BUY or SELL")

        if order.price <= 0:
            raise ValueError("Order price must be greater than zero")

        if order.quantity <= 0:
            raise ValueError("Order quantity must be greater than zero")

        if order.side == "BUY":
            self.buy_orders.append(order)
            # Highest buy price gets priority.
            self.buy_orders.sort(
                key=lambda order: order.price,
                reverse=True
            )

        elif order.side == "SELL":
            self.sell_orders.append(order)
            # Lowest sell price gets priority.
            self.sell_orders.sort(
                key=lambda order: order.price
            )

    def cancel_order(self, order_id):
        """Cancel a pending order using its ID."""
        for order in self.buy_orders:
            if order.order_id == order_id:
                self.buy_orders.remove(order)
                return True

        for order in self.sell_orders:
            if order.order_id == order_id:
                self.sell_orders.remove(order)
                return True

        return False

    def match_orders(self):
        while self.buy_orders and self.sell_orders:
            buy_order = self.buy_orders[0]
            sell_order = self.sell_orders[0]

            # A trade can happen only when the prices cross.
            if buy_order.price < sell_order.price:
                break

            trade_quantity = min(
                buy_order.quantity,
                sell_order.quantity
            )

            # Execute the trade at the sell order's price.
            trade_price = sell_order.price

            trade = {
                "buy_order_id": buy_order.order_id,
                "sell_order_id": sell_order.order_id,
                "price": trade_price,
                "quantity": trade_quantity
            }

            self.trades.append(trade)

            print("\nTrade Executed")
            print("Buy Order:", buy_order.order_id)
            print("Sell Order:", sell_order.order_id)
            print("Price:", trade_price)
            print("Quantity:", trade_quantity)

            buy_order.quantity -= trade_quantity
            sell_order.quantity -= trade_quantity

            if buy_order.quantity == 0:
                self.buy_orders.pop(0)

            if sell_order.quantity == 0:
                self.sell_orders.pop(0)

    def display(self):
        print("\nBUY ORDERS")

        if not self.buy_orders:
            print("No pending buy orders.")

        for order in self.buy_orders:
            print(
                "ID:", order.order_id,
                "Price:", order.price,
                "Quantity:", order.quantity
            )

        print("\nSELL ORDERS")

        if not self.sell_orders:
            print("No pending sell orders.")

        for order in self.sell_orders:
            print(
                "ID:", order.order_id,
                "Price:", order.price,
                "Quantity:", order.quantity
            )

    def display_trades(self):
        print("\nCOMPLETED TRADES")

        if not self.trades:
            print("No trades executed.")
            return

        for trade in self.trades:
            print(
                "BUY:", trade["buy_order_id"],
                "SELL:", trade["sell_order_id"],
                "PRICE:", trade["price"],
                "QUANTITY:", trade["quantity"]
            )

    def get_statistics(self):
        """Return summary statistics for the order book."""
        return {
            "pending_buy_orders": len(self.buy_orders),
            "pending_sell_orders": len(self.sell_orders),
            "pending_buy_quantity": sum(
                order.quantity for order in self.buy_orders
            ),
            "pending_sell_quantity": sum(
                order.quantity for order in self.sell_orders
            ),
            "total_trades": len(self.trades),
            "total_traded_quantity": sum(
                trade["quantity"] for trade in self.trades
            ),
        }

    def get_trade_summary(self):
        """Return a summary of completed trades."""
        if not self.trades:
            return {
                "total_trades": 0,
                "total_traded_quantity": 0,
                "average_trade_price": 0,
                "highest_trade_price": 0,
                "lowest_trade_price": 0,
            }

        prices = [trade["price"] for trade in self.trades]

        total_quantity = sum(
            trade["quantity"] for trade in self.trades
        )

        total_value = sum(
            trade["price"] * trade["quantity"]
            for trade in self.trades
        )

        return {
            "total_trades": len(self.trades),
            "total_traded_quantity": total_quantity,
            "average_trade_price": round(
                total_value / total_quantity, 2
            ),
            "highest_trade_price": max(prices),
            "lowest_trade_price": min(prices),
        }


if __name__ == "__main__":
    book = OrderBook()

    book.add_order(Order(1, "BUY", 110, 10))
    book.add_order(Order(2, "BUY", 105, 5))
    book.add_order(Order(3, "SELL", 108, 8))
    book.add_order(Order(4, "SELL", 109, 6))

    print("\nORDER BOOK BEFORE MATCHING")
    book.display()

    print("\nMATCHING ORDERS")
    book.match_orders()

    print("\nREMAINING ORDERS")
    book.display()

    book.display_trades()

    print("\nORDER BOOK STATISTICS")
    for name, value in book.get_statistics().items():
        print(f"{name}: {value}")

    print("\nTRADE SUMMARY")
    for name, value in book.get_trade_summary().items():
        print(f"{name}: {value}")
