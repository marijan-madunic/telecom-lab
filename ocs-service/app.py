import logging
from flask import Flask, jsonify

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 💰 Simulirani balance (u MB ili “kreditima”)
BALANCES = {
    "001010000000001": 1000,
    "001010000000002": 200,
    "001010000000003": 0,   # nema kredita
}

# 📊 koliko trošimo po requestu
USAGE_PER_REQUEST = 100

@app.route("/health")
def health():
    return {"status": "ok"}, 200

@app.route("/")
def home():
    return jsonify({"status": "OCS running"})


@app.route("/check/<imsi>", methods=["GET"])
def check_balance(imsi):
    balance = BALANCES.get(imsi, 0)

    logger.info(f"Checking balance for {imsi}: {balance}")

    if balance <= 0:
        return jsonify({
            "imsi": imsi,
            "allowed": False,
            "balance": balance
        })

    # simulacija potrošnje
    BALANCES[imsi] = max(0, balance - USAGE_PER_REQUEST)

    logger.info(f"New balance for {imsi}: {BALANCES[imsi]}")

    return jsonify({
        "imsi": imsi,
        "allowed": True,
        "balance": BALANCES[imsi]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8083)
