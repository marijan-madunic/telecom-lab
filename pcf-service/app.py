import os
import logging
from flask import Flask, request, jsonify
from prometheus_client import Counter, start_http_server

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

pcf_requests_total = Counter(
    "pcf_requests_total",
    "Total PCF policy requests"
)

pcf_policy_allowed_total = Counter(
    "pcf_policy_allowed_total",
    "Total allowed PCF policy decisions"
)

pcf_policy_denied_total = Counter(
    "pcf_policy_denied_total",
    "Total denied PCF policy decisions"
)

pcf_policy_errors_total = Counter(
    "pcf_policy_errors_total",
    "Total PCF policy errors"
)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/policy", methods=["POST"])
def policy():
    pcf_requests_total.inc()

    try:
        data = request.get_json()
        if not data:
            pcf_policy_errors_total.inc()
            return jsonify({"error": "Missing JSON body"}), 400

        imsi = data.get("imsi")
        session_type = data.get("session_type", "data")
        location = data.get("location", "unknown")

        if not imsi:
            pcf_policy_errors_total.inc()
            return jsonify({"error": "Missing imsi"}), 400

        logging.info(f"PCF request received for IMSI={imsi}, session_type={session_type}, location={location}")

        # Simple demo policy logic
        if imsi.endswith("999") or imsi.endswith("666"):
            pcf_policy_denied_total.inc()
            return jsonify({
                "imsi": imsi,
                "allowed": False,
                "reason": "subscriber_blocked"
            }), 403

        # Example QoS tiers based on IMSI suffix
        if imsi.endswith("001"):
            qos = "gold"
            max_bandwidth = "100Mbps"
        elif imsi.endswith("002"):
            qos = "silver"
            max_bandwidth = "50Mbps"
        else:
            qos = "bronze"
            max_bandwidth = "10Mbps"

        response = {
            "imsi": imsi,
            "session_type": session_type,
            "location": location,
            "allowed": True,
            "qos": qos,
            "max_bandwidth": max_bandwidth,
            "charging": "online"
        }

        pcf_policy_allowed_total.inc()
        return jsonify(response), 200

    except Exception as e:
        logging.exception("PCF policy error")
        pcf_policy_errors_total.inc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    metrics_port = int(os.getenv("METRICS_PORT", 8004))
    start_http_server(metrics_port)
    app.run(host="0.0.0.0", port=8084)
