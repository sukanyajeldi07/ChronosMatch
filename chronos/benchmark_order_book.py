
"""Week 2: Order Book performance benchmark."""

import io
import statistics
import time
from contextlib import redirect_stdout

from chronos.order_book import Order, OrderBook


ORDERS_PER_SIDE = 500
RUNS = 5


def run_benchmark():
    durations_ns = []
    total_trades = 0

    for run_number in range(RUNS):
        book = OrderBook()

        start_ns = time.perf_counter_ns()

        # Add 500 buy orders and 500 sell orders.
        # Prices are chosen so the orders can match.
        with redirect_stdout(io.StringIO()):
            for i in range(ORDERS_PER_SIDE):
                book.add_order(
                    Order(
                        f"B{run_number}-{i}",
                        "BUY",
                        2000 - i * 0.01,
                        1,
                    )
                )

            for i in range(ORDERS_PER_SIDE):
                book.add_order(
                    Order(
                        f"S{run_number}-{i}",
                        "SELL",
                        1000 + i * 0.01,
                        1,
                    )
                )

            book.match_orders()

        elapsed_ns = time.perf_counter_ns() - start_ns
        durations_ns.append(elapsed_ns)
        total_trades = len(book.trades)

    average_ns = statistics.mean(durations_ns)
    total_orders = ORDERS_PER_SIDE * 2

    print("\nCHRONOSMATCH WEEK 2 ORDER BOOK BENCHMARK")
    print("----------------------------------------")
    print(f"Runs: {RUNS}")
    print(f"Orders per run: {total_orders:,}")
    print(f"Trades in final run: {total_trades:,}")
    print(f"Average elapsed time: {average_ns / 1e6:.3f} ms")
    print(f"Average time per order: {average_ns / total_orders:.2f} ns")
    print(
        f"Order processing throughput: "
        f"{total_orders / (average_ns / 1e9):,.0f} orders/sec"
    )


if __name__ == "__main__":
    run_benchmark()
