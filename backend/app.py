
from flask import Flask, jsonify
from flask_cors import CORS

from chronos.matching_engine import MatchingEngine
from chronos.order_book import Order


app = Flask(__name__)
CORS(app)

# Create MatchingEngine
engine = MatchingEngine()


# Add sample BUY orders
engine.submit_order(Order(1, "BUY", 110, 10))
engine.submit_order(Order(2, "BUY", 105, 5))

# Add sample SELL orders
engine.submit_order(Order(3, "SELL", 108, 8))
engine.submit_order(Order(4, "SELL", 109, 6))

# Execute order matching
engine.execute()


@app.route("/")
def home():
    return jsonify({
        "project": "ChronosMatch",
        "status": "Backend API is running",
        "version": "1.0"
    })


@app.route("/api/metrics")
def metrics():
    return jsonify({
        "project": "ChronosMatch",

        "best_bid": engine.get_best_bid(),
        "best_ask": engine.get_best_ask(),
        "spread": engine.get_bid_ask_spread(),

        "execution_metrics": engine.get_execution_metrics(),

        "statistics": engine.get_statistics(),

        "trade_history": engine.get_trade_history()
    })


@app.route("/api/health")
def health():
    return jsonify({
        "status": "healthy",
        "engine": "running"
    })


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
