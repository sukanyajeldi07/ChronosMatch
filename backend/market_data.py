
"""
ChronosMatch - NSE Market Data Module
TrueData authorised live market feed.
"""

import json
import os
import sys
import time
import logging

from pathlib import Path
from datetime import datetime, timezone


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMPANIES_FILE = PROJECT_ROOT / "data" / "companies.json"
OUTPUT_FILE = PROJECT_ROOT / "backend" / "market_snapshot.json"


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

WAIT_SECONDS = 20
POLL_INTERVAL = 1


# --------------------------------------------------
# LOGGING
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("ChronosMatch.MarketData")


# --------------------------------------------------
# LOAD NSE COMPANIES
# --------------------------------------------------

def load_companies():

    if not COMPANIES_FILE.exists():
        raise FileNotFoundError(
            f"Company file not found: {COMPANIES_FILE}"
        )

    with open(COMPANIES_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, dict):
        companies = data.get(
            "companies",
            data.get("data", data)
        )
    else:
        companies = data

    if not isinstance(companies, (list, dict)):
        raise ValueError("Invalid companies.json format.")

    symbols = []

    symbol_keys = (
        "symbol",
        "nse_symbol",
        "tradingsymbol",
        "trading_symbol",
        "ticker"
    )

    entries = (
        companies.items()
        if isinstance(companies, dict)
        else enumerate(companies)
    )

    for _, company in entries:

        if isinstance(company, str):
            symbol = company

        elif isinstance(company, dict):
            symbol = next(
                (
                    company[key]
                    for key in symbol_keys
                    if company.get(key)
                ),
                None
            )
        else:
            symbol = None

        if symbol:
            symbol = str(symbol).strip().upper()

            if symbol and symbol not in symbols:
                symbols.append(symbol)

    if not symbols:
        raise ValueError("No NSE symbols found.")

    logger.info("Loaded %s company symbols.", len(symbols))

    return symbols


# --------------------------------------------------
# TRUEDATA CLIENT
# --------------------------------------------------

class ChronosMarketData:

    def __init__(self):

        self.username = os.getenv("TRUEDATA_USERNAME")
        self.password = os.getenv("TRUEDATA_PASSWORD")

        self.connection = None
        self.symbols = []
        self.request_ids = []

    # --------------------------------------------------
    # CONNECT
    # --------------------------------------------------

    def connect(self):

        if not self.username or not self.password:
            raise RuntimeError(
                "TrueData credentials are missing. "
                "Set TRUEDATA_USERNAME and TRUEDATA_PASSWORD."
            )

        try:
            from truedata import TD_live

        except ImportError as error:
            raise RuntimeError(
                "TrueData package is missing. "
                "Install it using: python -m pip install truedata"
            ) from error

        logger.info("Connecting to TrueData...")

        self.connection = TD_live(
            self.username,
            self.password
        )

        logger.info("TrueData connection initialized.")

    # --------------------------------------------------
    # SUBSCRIBE TO STOCKS
    # --------------------------------------------------

    def subscribe(self, symbols):

        if self.connection is None:
            raise RuntimeError("TrueData connection not initialized.")

        self.symbols = symbols

        logger.info(
            "Subscribing to %s NSE stocks...",
            len(symbols)
        )

        self.request_ids = self.connection.start_live_data(
            symbols
        ) or []

        logger.info(
            "Subscription request completed. Request IDs: %s",
            len(self.request_ids)
        )

    # --------------------------------------------------
    # READ TICK FIELD
    # --------------------------------------------------

    @staticmethod
    def read_field(tick, field):

        if isinstance(tick, dict):
            return tick.get(field)

        return getattr(tick, field, None)

    # --------------------------------------------------
    # GET MARKET SNAPSHOT
    # --------------------------------------------------

    def get_market_snapshot(self):

        if self.connection is None:
            raise RuntimeError("TrueData is not connected.")

        live_data = self.connection.live_data

        results = []

        for index, symbol in enumerate(self.symbols):

            tick = None

            # TrueData versions may expose data using request IDs.
            if index < len(self.request_ids):
                tick = live_data.get(self.request_ids[index])

            # Compatibility fallback for symbol-keyed feeds.
            if tick is None:
                tick = live_data.get(symbol)

            if tick is None:
                continue

            record = {
                "symbol": symbol,
                "ltp": self.read_field(tick, "ltp"),
                "change": self.read_field(tick, "change"),
                "change_percent": self.read_field(
                    tick, "change_perc"
                ),
                "volume": self.read_field(tick, "ttq"),
                "open": self.read_field(tick, "day_open"),
                "high": self.read_field(tick, "day_high"),
                "low": self.read_field(tick, "day_low"),
                "previous_close": self.read_field(
                    tick, "prev_day_close"
                ),
                "timestamp": str(
                    self.read_field(tick, "timestamp")
                ),
                "source": "TrueData",
                "data_type": "LIVE"
            }

            results.append(record)

        return {
            "project": "ChronosMatch",
            "source": "TrueData",
            "data_type": "LIVE",
            "updated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "total_symbols": len(self.symbols),
            "received_symbols": len(results),
            "market_data": results
        }

    # --------------------------------------------------
    # WAIT FOR MARKET DATA
    # --------------------------------------------------

    def wait_for_market_data(self):

        logger.info("Waiting for live stock updates...")

        deadline = time.monotonic() + WAIT_SECONDS

        while time.monotonic() < deadline:

            snapshot = self.get_market_snapshot()

            if snapshot["received_symbols"] > 0:
                return snapshot

            time.sleep(POLL_INTERVAL)

        raise TimeoutError(
            "No market ticks received within "
            f"{WAIT_SECONDS} seconds. Check market hours, "
            "subscription and TrueData connection."
        )

    # --------------------------------------------------
    # SAVE JSON SNAPSHOT
    # --------------------------------------------------

    def save_snapshot(self, snapshot):

        OUTPUT_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            OUTPUT_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                snapshot,
                file,
                indent=4,
                default=str
            )

        logger.info("Market snapshot saved: %s", OUTPUT_FILE)

    # --------------------------------------------------
    # DISCONNECT
    # --------------------------------------------------

    def disconnect(self):

        if self.connection is None:
            return

        try:

            if self.symbols:
                self.connection.stop_live_data(self.symbols)

            self.connection.disconnect()

            logger.info("TrueData disconnected.")

        except Exception as error:

            logger.warning(
                "Disconnect warning: %s",
                error
            )

        finally:
            self.connection = None


# --------------------------------------------------
# MAIN PROGRAM
# --------------------------------------------------

def main():

    client = ChronosMarketData()

    try:

        print("\n================================")
        print("     CHRONOSMATCH MARKET DATA")
        print("================================")

        symbols = load_companies()

        print("Companies :", len(symbols))
        print("Provider  : TrueData")
        print("Mode      : LIVE")

        client.connect()

        client.subscribe(symbols)

        snapshot = client.wait_for_market_data()

        client.save_snapshot(snapshot)

        print("\n================================")
        print("       MARKET DATA SUMMARY")
        print("================================")

        print(
            "Received:",
            snapshot["received_symbols"],
            "/",
            snapshot["total_symbols"]
        )

        for stock in snapshot["market_data"]:

            print(
                stock["symbol"],
                "| LTP:", stock["ltp"],
                "| Change %:", stock["change_percent"],
                "| Volume:", stock["volume"]
            )

        print("\nSnapshot saved successfully.")

    except Exception as error:

        logger.error("Market data error: %s", error)

        return 1

    finally:

        client.disconnect()

    return 0


if __name__ == "__main__":
    sys.exit(main())
