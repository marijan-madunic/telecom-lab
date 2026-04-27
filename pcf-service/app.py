import os
import logging
import requests
from flask import Flask, request, jsonify
from prometheus_client import Counter, start_http_server

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

UDM_URL = os.getenv("UDM_URL", "http://udm-service:8082")

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
        data = request.get_json(silent=True) or {}

        imsi = data.get("imsi")
        session_type = data.get("session_type", "data")
        location = data.get("location", "unknown")

        if not imsi:
            pcf_policy_errors_total.inc()
            return jsonify({"error": "Missing imsi"}), 400

        logging.info(
            f"PCF request received for IMSI={imsi}, "
            f"session_type={session_type}, location={location}"
        )

        try:
            udm_response = requests.get(f"{UDM_URL}/policy/{imsi}", timeout=3)
        except requests.exceptions.RequestException as e:
            logging.exception("UDM unreachable from PCF")
            pcf_policy_errors_total.inc()
            return jsonify({
                "status": "ERROR",
                "reason": "UDM unreachable",
                "error": str(e)
            }), 500

        udm_data = udm_response.json()

        if udm_response.status_code == 404:
            pcf_policy_denied_total.inc()
            return jsonify({
                "imsi": imsi,
                "allowed": False,
                "reason": "subscriber_not_found",
                "udm_response": udm_data
            }), 404

        if udm_response.status_code != 200:
            pcf_policy_denied_total.inc()
            return jsonify({
                "imsi": imsi,
                "allowed": False,
                "reason": "udm_policy_lookup_failed",
                "udm_response": udm_data
            }), 403

        if udm_data.get("access_restriction"):
            pcf_policy_denied_total.inc()
            return jsonify({
                "imsi": imsi,
                "session_type": session_type,
                "location": location,
                "allowed": False,
                "reason": "access_restriction_enabled",
                "source": "UDM"
            }), 403

        qos_profile = udm_data.get("qos_profile", "unknown")
        plan = udm_data.get("plan", "unknown")

        response = {
            "imsi": imsi,
            "session_type": session_type,
            "location": location,
            "allowed": True,
            "plan": plan,
            "qos_profile": qos_profile,
            "roaming_enabled": udm_data.get("roaming_enabled"),
            "max_sessions": udm_data.get("max_sessions"),
            "charging": "online",
            "source": "UDM"
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
