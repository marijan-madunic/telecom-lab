from flask import Flask, jsonify

app = Flask(__name__)

#  Simulirani subscriber podaci
SUBSCRIBERS = {
    "001010000000001": {
        "plan": "gold",
        "is_roaming": False,
        "key": "secret123",
        "opc": "opc123",
        "qos_profile": {
            "qci": 7,
            "arp": 1,
            "max_ul_mbps": 100,
            "max_dl_mbps": 500
        },
        "allowed_services": ["internet", "volte", "streaming"]
    },
    "001010000000002": {
        "plan": "gold",
        "is_roaming": True,
        "key": "secret456",
        "opc": "opc456",
        "qos_profile": {
            "qci": 8,
            "arp": 2,
            "max_ul_mbps": 50,
            "max_dl_mbps": 200
        },
        "allowed_services": ["internet", "volte"]
    },
    "001010000000003": {
        "plan": "silver",
        "is_roaming": False,
        "key": "secret789",
        "opc": "opc789",
        "qos_profile": {
            "qci": 9,
            "arp": 3,
            "max_ul_mbps": 20,
            "max_dl_mbps": 100
        },
        "allowed_services": ["internet"]
    },

    "001010000000004": {"plan": "bronze", "is_roaming": True},

    "001010000000005": {"plan": "gold", "is_roaming": False},
    "001010000000006": {"plan": "silver", "is_roaming": True},
    "001010000000007": {"plan": "bronze", "is_roaming": False},

    "001010000000008": {"plan": "gold", "is_roaming": False},
    "001010000000009": {"plan": "silver", "is_roaming": False},
    "001010000000010": {"plan": "bronze", "is_roaming": True},
}

@app.route("/health")
def health():
    return {"status": "ok"}, 200

@app.route("/subscriber/<imsi>", methods=["GET"])
def subscriber(imsi):
    data = SUBSCRIBERS.get(imsi)

    if not data:
        return jsonify({"error": "subscriber not found"}), 404

    result = {
        "imsi": imsi,
        "profile": {
            "plan": data["plan"],
            "is_roaming": data["is_roaming"]
        },
        "auth": {
            "key": data.get("key"),
            "opc": data.get("opc")
        },
        "qos_profile": data.get("qos_profile", {}),
        "allowed_services": data.get("allowed_services", [])
    }

    return jsonify(result)

@app.route("/auth/<imsi>", methods=["GET"])
def auth_data(imsi):
    data = SUBSCRIBERS.get(imsi)

    if not data:
        return jsonify({"error": "subscriber not found"}), 404

    result = {
        "imsi": imsi,
        "key": data.get("key"),
        "opc": data.get("opc")
    }

    return jsonify(result)

@app.route("/policy/<imsi>", methods=["GET"])
def policy_data(imsi):
    data = SUBSCRIBERS.get(imsi)

    if not data:
        return jsonify({"error": "subscriber not found"}), 404

    result = {
        "imsi": imsi,
        "plan": data["plan"],
        "is_roaming": data["is_roaming"],
        "qos_profile": data.get("qos_profile", {}),
        "allowed_services": data.get("allowed_services", [])
    }

    return jsonify(result)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "UDM service running"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082)
