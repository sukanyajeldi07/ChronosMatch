
"""ChronosMatch weekly zero-copy IPC benchmark.

Measures:
- Consumer throughput (orders/second)
- Orders processed
- Mean latency (milliseconds)
- P99 latency (milliseconds)

Saves measured results to benchmark_results.json.
"""

import argparse
import asyncio
import ctypes
import json
import multiprocessing as mp
import os
import queue
import sys
import tempfile
import time
from pathlib import Path

if sys.platform == "win32":
    try:
        ctypes.windll.winmm.timeBeginPeriod(1)
    except Exception:
        pass

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from chronos.consumer import ZeroCopyConsumer
from chronos.firehose import MarketFirehose
from chronos.ring_buffer import MmapRingBuffer


def producer_process(filepath, num_orders, target_rate, batch_size):
    buffer = MmapRingBuffer(filepath, create=False)

    try:
        firehose = MarketFirehose(
            buffer,
            target_rate=target_rate,
            batch_size=batch_size
        )

        time.sleep(0.05)

        stats = asyncio.run(
            firehose.blast(
                total_orders=num_orders,
                print_progress=False
            )
        )

        print(
            f"Producer sent {stats.total_orders_sent:,} orders "
            f"in {stats.elapsed_time:.3f}s"
        )
    finally:
        buffer.close()


def consumer_process(filepath, num_orders, batch_size, result_queue):
    buffer = MmapRingBuffer(filepath, create=False)

    try:
        consumer = ZeroCopyConsumer(
            buffer,
            batch_size=batch_size
        )

        stats = consumer.run(
            total_orders=num_orders,
            print_progress=False
        )

        result_queue.put({
            "orders": stats.total_orders_read,
            "elapsed_seconds": stats.elapsed_time,
            "throughput": stats.avg_rate,
            "mean_latency_ms": stats.avg_latency_us / 1000,
            "p99_latency_ms": stats.p99_latency_us / 1000,
            "min_latency_ms": stats.min_latency_us / 1000,
            "max_latency_ms": stats.max_latency_us / 1000
        })
    finally:
        buffer.close()


def save_weekly_result(week, result):
    result_file = ROOT / "benchmark_results.json"

    if result_file.exists():
        try:
            with result_file.open("r", encoding="utf-8") as file:
                all_results = json.load(file)
        except (json.JSONDecodeError, OSError):
            all_results = {}
    else:
        all_results = {}

    all_results[f"week_{week}"] = result

    with result_file.open("w", encoding="utf-8") as file:
        json.dump(all_results, file, indent=4)

    print(f"\nSaved results to: {result_file}")


def run_benchmark(week, num_orders, target_rate, batch_size):
    print("\n" + "=" * 65)
    print(f"CHRONOSMATCH - WEEK {week} IPC BENCHMARK")
    print("=" * 65)
    print(f"Orders       : {num_orders:,}")
    print(f"Target rate  : {target_rate:,} orders/second")
    print(f"Batch size   : {batch_size}")

    fd, tmp_path = tempfile.mkstemp(
        prefix="chronos_bench_",
        suffix=".bin"
    )
    os.close(fd)

    result_queue = mp.Queue()
    producer = None
    consumer = None

    try:
        capacity = 524_288

        ring_buffer = MmapRingBuffer(
            tmp_path,
            capacity=capacity,
            create=True
        )
        ring_buffer.close()

        consumer = mp.Process(
            target=consumer_process,
            args=(tmp_path, num_orders, batch_size, result_queue)
        )

        producer = mp.Process(
            target=producer_process,
            args=(tmp_path, num_orders, target_rate, batch_size)
        )

        print("\nStarting consumer...")
        consumer.start()

        print("Starting producer...")
        producer.start()

        producer.join()
        consumer.join()

        if producer.exitcode != 0:
            raise RuntimeError(
                f"Producer failed with exit code {producer.exitcode}"
            )

        if consumer.exitcode != 0:
            raise RuntimeError(
                f"Consumer failed with exit code {consumer.exitcode}"
            )

        try:
            result = result_queue.get(timeout=5)
        except queue.Empty:
            raise RuntimeError("Consumer did not return benchmark results.")

        if result["orders"] <= 0:
            raise RuntimeError("No orders were processed.")

        print("\n" + "=" * 65)
        print(f"WEEK {week} - MEASURED RESULTS")
        print("=" * 65)

        print(f"Orders processed  : {result['orders']:,}")
        print(f"Consumer throughput: {result['throughput']:,.0f} orders/sec")
        print(f"Mean latency      : {result['mean_latency_ms']:.3f} ms")
        print(f"P99 latency       : {result['p99_latency_ms']:.3f} ms")
        print(f"Elapsed time      : {result['elapsed_seconds']:.3f} seconds")
        print("=" * 65)

        result["week"] = week
        result["target_rate"] = target_rate
        result["batch_size"] = batch_size
        result["measured_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

        save_weekly_result(week, result)

    finally:
        for process in (producer, consumer):
            if process is not None and process.is_alive():
                process.terminate()
                process.join()

        result_queue.close()

        try:
            os.remove(tmp_path)
        except OSError:
            pass


if __name__ == "__main__":
    mp.freeze_support()

    parser = argparse.ArgumentParser(
        description="ChronosMatch weekly IPC benchmark"
    )

    parser.add_argument(
        "--week",
        type=int,
        choices=[1, 2, 3, 4],
        required=True
    )

    parser.add_argument(
        "--orders",
        type=int,
        default=300_000
    )

    parser.add_argument(
        "--rate",
        type=int,
        default=100_000
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=500
    )

    args = parser.parse_args()

    if args.orders <= 0 or args.rate <= 0 or args.batch_size <= 0:
        parser.error("Orders, rate and batch size must be positive.")

    run_benchmark(
        week=args.week,
        num_orders=args.orders,
        target_rate=args.rate,
        batch_size=args.batch_size
    )
