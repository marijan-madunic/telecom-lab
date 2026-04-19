import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

UDM_URL = "http://udm-service:8082"


@app.route("/authenticate", methods=["POST"])
def authenticate():
    data = request.get_json()
    imsi = data.get("imsi")

    if not imsi:
        return jsonify({"status": "ERROR", "error": "missing imsi"}), 400

    try:
        r = requests.get(f"{UDM_URL}/auth/{imsi}", timeout=3)

        if r.status_code != 200:
            return jsonify({
                "status": "FAIL",
                "reason": "subscriber not found"
            }), 401

        auth_data = r.json()

        if not auth_data.get("key") or not auth_data.get("opc"):
            return jsonify({
                "status": "FAIL",
                "reason": "missing auth data"
            }), 401

        return jsonify({
            "status": "SUCCESS",
            "imsi": imsi,
            "auth_token": f"token-{imsi}"
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "ERROR",
            "error": str(e)
        }), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "AUSF service running"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8085)
