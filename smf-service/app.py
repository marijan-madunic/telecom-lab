import os
import json
import uuid
import ipaddress
import logging
from typing import Dict, Any, Optional

import redis
import requests
from flask import Flask, jsonify, request
from prometheus_client import Counter, Gauge, start_http_server

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
UDM_URL = os.getenv("UDM_URL", "http://udm-service:8081")
SMF_METRICS_PORT = int(os.getenv("SMF_METRICS_PORT", "8001"))
IP_POOL_SUBNET = os.getenv("IP_POOL_SUBNET", "10.20.0.0/24")

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

smf_session_create_requests_total = Counter(
    "smf_session_create_requests_total",
    "Total SMF session create requests"
)

smf_session_create_success_total = Counter(
    "smf_session_create_success_total",
    "Total successful SMF session creations"
)

smf_session_create_fail_total = Counter(
    "smf_session_create_fail_total",
    "Total failed SMF session creations"
)

smf_session_delete_total = Counter(
    "smf_session_delete_total",
    "Total SMF session deletions"
)

smf_sessions_active = Gauge(
    "smf_sessions_active",
    "Current number of active SMF sessions"
)


def allocate_fake_ip() -> str:
    """
    Very simple IP allocator for lab/demo purposes.
    Scans a small subnet and returns the first free host IP.
    """
    network = ipaddress.ip_network(IP_POOL_SUBNET)
    for host in network.hosts():
        ip_str = str(host)
        key = f"smf:ip:{ip_str}"
        if not redis_client.exists(key):
            redis_client.set(key, "allocated")
            return ip_str
    raise RuntimeError("No free IP addresses available in the pool")


def release_fake_ip(ip_address: str) -> None:
    redis_client.delete(f"smf:ip:{ip_address}")


def get_subscriber_from_udm(imsi: str) -> Optional[Dict[str, Any]]:
    """
    Adjust this path to match your real UDM API.
    Example assumption:
      GET /subscriber/<imsi>
    """
    try:
        response = requests.get(
            f"{UDM_URL}/subscriber/{imsi}",
            timeout=3
        )
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException as exc:
        app.logger.error("UDM request failed: %s", exc)
        return None


def build_session_payload(
    imsi: str,
    dnn: str,
    s_nssai: str,
    ip_address: str,
    subscriber: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    session_id = f"sess-{uuid.uuid4().hex[:12]}"
    qos_profile = "default"

    if subscriber:
        qos_profile = subscriber.get("plan", "default")

    return {
        "session_id": session_id,
        "imsi": imsi,
        "dnn": dnn,
        "s_nssai": s_nssai,
        "ip_address": ip_address,
        "qos_profile": qos_profile,
        "status": "active"
    }


@app.route("/health", methods=["GET"])
def health() -> Any:
    return jsonify({"status": "ok", "service": "smf-service"}), 200


@app.route("/sessions", methods=["POST"])
def create_session() -> Any:
    smf_session_create_requests_total.inc()

    try:
        payload = request.get_json(force=True)
        imsi = payload.get("imsi")
        dnn = payload.get("dnn", "internet")
        s_nssai = payload.get("slice", "1-010203")

        if not imsi:
            smf_session_create_fail_total.inc()
            return jsonify({"error": "Missing required field: imsi"}), 400

        subscriber = get_subscriber_from_udm(imsi)
        if not subscriber:
            smf_session_create_fail_total.inc()
            return jsonify({"error": "Subscriber not found in UDM"}), 404

        allowed_dnns = ["internet"]
        if dnn not in allowed_dnns:
            smf_session_create_fail_total.inc()
            return jsonify({"error": f"DNN '{dnn}' not allowed for subscriber"}), 403

        ip_address = allocate_fake_ip()
        session = build_session_payload(imsi, dnn, s_nssai, ip_address, subscriber)

        redis_client.set(
            f"smf:session:{session['session_id']}",
            json.dumps(session)
        )

        redis_client.sadd(f"smf:imsi:{imsi}:sessions", session["session_id"])

        smf_session_create_success_total.inc()
        smf_sessions_active.inc()

        return jsonify(session), 201

    except RuntimeError as exc:
        smf_session_create_fail_total.inc()
        return jsonify({"error": str(exc)}), 503

    except Exception as exc:
        app.logger.exception("Unexpected error while creating session")
        smf_session_create_fail_total.inc()
        return jsonify({"error": f"Internal error: {exc}"}), 500


@app.route("/sessions/<session_id>", methods=["GET"])
def get_session(session_id: str) -> Any:
    raw_session = redis_client.get(f"smf:session:{session_id}")
    if not raw_session:
        return jsonify({"error": "Session not found"}), 404

    return jsonify(json.loads(raw_session)), 200


@app.route("/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id: str) -> Any:
    raw_session = redis_client.get(f"smf:session:{session_id}")
    if not raw_session:
        return jsonify({"error": "Session not found"}), 404

    session = json.loads(raw_session)
    imsi = session["imsi"]
    ip_address = session["ip_address"]

    redis_client.delete(f"smf:session:{session_id}")
    redis_client.srem(f"smf:imsi:{imsi}:sessions", session_id)
    release_fake_ip(ip_address)

    smf_session_delete_total.inc()
    smf_sessions_active.dec()

    return jsonify({
        "message": "Session deleted",
        "session_id": session_id
    }), 200


@app.route("/sessions/imsi/<imsi>", methods=["GET"])
def list_sessions_for_imsi(imsi: str) -> Any:
    session_ids = list(redis_client.smembers(f"smf:imsi:{imsi}:sessions"))
    sessions = []

    for session_id in session_ids:
        raw_session = redis_client.get(f"smf:session:{session_id}")
        if raw_session:
            sessions.append(json.loads(raw_session))

    return jsonify({
        "imsi": imsi,
        "sessions": sessions
    }), 200


if __name__ == "__main__":
    start_http_server(SMF_METRICS_PORT)
    app.run(host="0.0.0.0", port=8083)
