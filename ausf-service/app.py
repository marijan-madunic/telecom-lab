import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

UDM_URL = os.getenv("UDM_URL", "http://udm-service:8082")


@app.route("/authenticate", methods=["POST"])
def authenticate():
    data = request.get_json(silent=True) or {}
    imsi = data.get("imsi")

    if not imsi:
        return jsonify({"status": "ERROR", "error": "missing imsi"}), 400

    try:
        r = requests.get(f"{UDM_URL}/auth/{imsi}", timeout=3)
    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "ERROR",
            "reason": "UDM unreachable",
            "error": str(e)
        }), 500

    udm_data = r.json()

    if r.status_code == 404:
        return jsonify({
            "status": "FAIL",
            "reason": "subscriber not found",
            "udm_response": udm_data
        }), 404

    if r.status_code != 200:
        return jsonify({
            "status": "FAIL",
            "reason": udm_data.get("reason", "authentication rejected by UDM"),
            "udm_response": udm_data
        }), 403

    if not udm_data.get("auth_allowed"):
        return jsonify({
            "status": "FAIL",
            "reason": udm_data.get("reason", "authentication not allowed"),
            "udm_response": udm_data
        }), 403

    return jsonify({
        "status": "SUCCESS",
        "imsi": imsi,
        "auth_token": f"token-{imsi}",
        "source": "UDM"
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "AUSF service running with UDM backend"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8085)
