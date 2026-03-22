from flask import Flask, jsonify

app = Flask(__name__)

# 🔹 Simulirani subscriber podaci
SUBSCRIBERS = {
    "001010000000001": {"plan": "gold", "is_roaming": False},
    "001010000000002": {"plan": "gold", "is_roaming": True},
    "001010000000003": {"plan": "silver", "is_roaming": False},
    "001010000000004": {"plan": "bronze", "is_roaming": True},
}

@app.route("/health")
def health():
    return {"status": "ok"}, 200

@app.route("/subscriber/<imsi>", methods=["GET"])
def subscriber(imsi):
    data = SUBSCRIBERS.get(imsi)
    if data:
        result = {
            "imsi": imsi,
            "plan": data["plan"],
            "is_roaming": data["is_roaming"]
        }
        return jsonify(result)
    else:
        return jsonify({"error": "subscriber not found"}), 404


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "UDM service running"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082)
