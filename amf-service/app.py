import os
import uuid
import logging
import requests
import redis
from flask import Flask, request, jsonify
from prometheus_client import Counter, start_http_server

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

amf_register_requests_total = Counter(
    "amf_register_requests_total",
    "Total AMF register requests"
)

amf_registrations_total = Counter(
    "amf_registrations_total",
    "Total successful AMF registrations"
)

amf_pdu_session_requests_total = Counter(
    "amf_pdu_session_requests_total",
    "Total AMF PDU session requests"
)

amf_pdu_sessions_created_total = Counter(
    "amf_pdu_sessions_created_total",
    "Total successful AMF PDU sessions created"
)

amf_auth_failures_total = Counter(
    "amf_auth_failures_total",
    "Total AMF authentication failures"
)

amf_errors_total = Counter(
    "amf_errors_total",
    "Total AMF internal errors"
)

AUSF_URL = os.getenv("AUSF_URL", "http://ausf-service:8085")
SMF_URL = os.getenv("SMF_URL", "http://smf-service:8083")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
SESSION_TTL = int(os.getenv("SESSION_TTL", "3600"))

rds = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

start_http_server(8006)


@app.route("/register", methods=["POST"])
def register():
    amf_register_requests_total.inc()

    data = request.get_json(silent=True) or {}
    imsi = data.get("imsi")

    if not imsi:
        return jsonify({
            "status": "ERROR",
            "error": "missing imsi"
        }), 400

    try:
        logger.info("Register request received for IMSI=%s", imsi)

        auth_resp = requests.post(
            f"{AUSF_URL}/authenticate",
            json={"imsi": imsi},
            timeout=3
        )

        if auth_resp.status_code != 200:
            amf_auth_failures_total.inc()
            logger.warning("Authentication failed for IMSI=%s", imsi)
            return jsonify({
                "status": "AUTH_FAILED",
                "imsi": imsi
            }), 401

        auth_data = auth_resp.json()
        if auth_data.get("status") != "SUCCESS":
            amf_auth_failures_total.inc()
            logger.warning("Authentication unsuccessful for IMSI=%s", imsi)
            return jsonify({
                "status": "AUTH_FAILED",
                "imsi": imsi
            }), 401

        session_id = f"sess-{uuid.uuid4().hex[:10]}"
        rds.setex(f"amf:session:{imsi}", SESSION_TTL, session_id)

        amf_registrations_total.inc()
        logger.info("Session created for IMSI=%s session_id=%s", imsi, session_id)

        return jsonify({
            "status": "REGISTERED",
            "imsi": imsi,
            "session_id": session_id
        }), 200

    except requests.exceptions.RequestException as e:
        amf_errors_total.inc()
        logger.error("AUSF request failed for IMSI=%s error=%s", imsi, str(e))
        return jsonify({
            "status": "ERROR",
            "error": "ausf unavailable"
        }), 503

    except redis.exceptions.RedisError as e:
        amf_errors_total.inc()
        logger.error("Redis error for IMSI=%s error=%s", imsi, str(e))
        return jsonify({
            "status": "ERROR",
            "error": "redis unavailable"
        }), 503

    except Exception:
        amf_errors_total.inc()
        logger.exception("Unexpected error during registration for IMSI=%s", imsi)
        return jsonify({
            "status": "ERROR",
            "error": "internal server error"
        }), 500


@app.route("/pdu-session", methods=["POST"])
def create_pdu_session():
    amf_pdu_session_requests_total.inc()

    data = request.get_json(silent=True) or {}
    imsi = data.get("imsi")
    dnn = data.get("dnn", "internet")

    if not imsi:
        return jsonify({
            "status": "ERROR",
            "error": "missing imsi"
        }), 400

    try:
        logger.info("PDU session request received for IMSI=%s DNN=%s", imsi, dnn)

        amf_session_id = rds.get(f"amf:session:{imsi}")
        if not amf_session_id:
            return jsonify({
                "status": "ERROR",
                "error": "ue not registered",
                "imsi": imsi
            }), 404

        smf_resp = requests.post(
            f"{SMF_URL}/sessions",
            json={
                "imsi": imsi,
                "dnn": dnn
            },
            timeout=5
        )

        if smf_resp.status_code not in (200, 201):
            amf_errors_total.inc()
            logger.warning(
                "SMF session creation failed for IMSI=%s status_code=%s",
                imsi,
                smf_resp.status_code
            )
            return jsonify({
                "status": "SMF_FAILED",
                "imsi": imsi,
                "smf_status_code": smf_resp.status_code
            }), 502

        smf_data = smf_resp.json()

        amf_pdu_sessions_created_total.inc()
        logger.info("PDU session created via SMF for IMSI=%s", imsi)

        return jsonify({
            "status": "PDU_SESSION_CREATED",
            "imsi": imsi,
            "amf_session_id": amf_session_id,
            "smf_response": smf_data
        }), 201

    except requests.exceptions.RequestException as e:
        amf_errors_total.inc()
        logger.error("SMF request failed for IMSI=%s error=%s", imsi, str(e))
        return jsonify({
            "status": "ERROR",
            "error": "smf unavailable"
        }), 503

    except redis.exceptions.RedisError as e:
        amf_errors_total.inc()
        logger.error("Redis error during PDU session creation for IMSI=%s error=%s", imsi, str(e))
        return jsonify({
            "status": "ERROR",
            "error": "redis unavailable"
        }), 503

    except Exception:
        amf_errors_total.inc()
        logger.exception("Unexpected error during PDU session creation for IMSI=%s", imsi)
        return jsonify({
            "status": "ERROR",
            "error": "internal server error"
        }), 500


@app.route("/sessions/<imsi>", methods=["GET"])
def get_session(imsi):
    try:
        session_id = rds.get(f"amf:session:{imsi}")

        if not session_id:
            return jsonify({
                "status": "NOT_FOUND",
                "error": "session not found",
                "imsi": imsi
            }), 404

        return jsonify({
            "status": "FOUND",
            "imsi": imsi,
            "session_id": session_id
        }), 200

    except redis.exceptions.RedisError as e:
        amf_errors_total.inc()
        logger.error("Redis error while fetching session for IMSI=%s error=%s", imsi, str(e))
        return jsonify({
            "status": "ERROR",
            "error": "redis unavailable"
        }), 503


@app.route("/health", methods=["GET"])
def health():
    try:
        rds.ping()
        return jsonify({
            "status": "ok",
            "service": "amf",
            "redis": "ok"
        }), 200
    except redis.exceptions.RedisError:
        amf_errors_total.inc()
        return jsonify({
            "status": "degraded",
            "service": "amf",
            "redis": "unavailable"
        }), 503


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "service": "amf"
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8086)
