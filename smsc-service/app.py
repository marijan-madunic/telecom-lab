import os
import json
import uuid
import time
import logging
import redis
from flask import Flask, request, jsonify
from prometheus_client import Counter, Gauge, start_http_server

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
SMSC_HTTP_PORT = int(os.getenv("SMSC_HTTP_PORT", "8080"))
SMSC_METRICS_PORT = int(os.getenv("SMSC_METRICS_PORT", "8001"))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

sms_requests_total = Counter(
    "sms_requests_total",
    "Total number of SMS API requests"
)

sms_sent_total = Counter(
    "sms_sent_total",
    "Total number of SMS messages accepted for delivery"
)

sms_delivered_total = Counter(
    "sms_delivered_total",
    "Total number of SMS messages delivered"
)

sms_failed_total = Counter(
    "sms_failed_total",
    "Total number of SMS messages failed"
)

sms_status_checks_total = Counter(
    "sms_status_checks_total",
    "Total number of SMS status checks"
)

sms_inbox_reads_total = Counter(
    "sms_inbox_reads_total",
    "Total number of inbox read requests"
)

sms_pending_gauge = Gauge(
    "sms_pending_messages",
    "Current number of pending SMS messages"
)


def validate_msisdn(value: str) -> bool:
    return isinstance(value, str) and value.isdigit() and 6 <= len(value) <= 15


def update_pending_gauge():
    try:
        keys = redis_client.keys("sms:*")
        pending_count = 0

        for key in keys:
            if key.startswith("sms:inbox:"):
                continue
            raw = redis_client.get(key)
            if not raw:
                continue
            msg = json.loads(raw)
            if msg.get("status") == "PENDING":
                pending_count += 1

        sms_pending_gauge.set(pending_count)
    except Exception as exc:
        logging.warning("Failed to update pending gauge: %s", exc)


@app.route("/health", methods=["GET"])
def health():
    try:
        redis_client.ping()
        return jsonify({"status": "UP"}), 200
    except Exception as exc:
        logging.error("Health check failed: %s", exc)
        return jsonify({"status": "DOWN", "error": str(exc)}), 500


@app.route("/send_sms", methods=["POST"])
def send_sms():
    sms_requests_total.inc()

    try:
        data = request.get_json(force=True)

        sender = data.get("from")
        recipient = data.get("to")
        text = data.get("text")

        if not sender or not recipient or not text:
            return jsonify({
                "error": "Fields 'from', 'to', and 'text' are required"
            }), 400

        if not validate_msisdn(sender) or not validate_msisdn(recipient):
            return jsonify({
                "error": "Invalid MSISDN format in 'from' or 'to'"
            }), 400

        if not isinstance(text, str) or not text.strip():
            return jsonify({
                "error": "Field 'text' must be a non-empty string"
            }), 400

        message_id = str(uuid.uuid4())
        created_at = int(time.time())

        sms_record = {
            "message_id": message_id,
            "from": sender,
            "to": recipient,
            "text": text.strip(),
            "status": "PENDING",
            "created_at": created_at
        }

        redis_client.set(f"sms:{message_id}", json.dumps(sms_record))
        redis_client.rpush(f"sms:inbox:{recipient}", message_id)

        sms_sent_total.inc()

        # Simple demo delivery logic:
        # If text contains FAIL, simulate failed delivery
        if "FAIL" in text.upper():
            sms_record["status"] = "FAILED"
            redis_client.set(f"sms:{message_id}", json.dumps(sms_record))
            sms_failed_total.inc()
        else:
            sms_record["status"] = "DELIVERED"
            redis_client.set(f"sms:{message_id}", json.dumps(sms_record))
            sms_delivered_total.inc()

        update_pending_gauge()

        return jsonify(sms_record), 201

    except Exception as exc:
        logging.exception("Error while sending SMS")
        return jsonify({"error": str(exc)}), 500


@app.route("/sms/<message_id>/status", methods=["GET"])
def get_sms_status(message_id):
    sms_status_checks_total.inc()

    try:
        raw = redis_client.get(f"sms:{message_id}")
        if not raw:
            return jsonify({"error": "Message not found"}), 404

        sms_record = json.loads(raw)
        return jsonify({
            "message_id": sms_record["message_id"],
            "status": sms_record["status"]
        }), 200

    except Exception as exc:
        logging.exception("Error while checking SMS status")
        return jsonify({"error": str(exc)}), 500


@app.route("/messages/<msisdn>", methods=["GET"])
def get_messages(msisdn):
    sms_inbox_reads_total.inc()

    try:
        if not validate_msisdn(msisdn):
            return jsonify({"error": "Invalid MSISDN format"}), 400

        message_ids = redis_client.lrange(f"sms:inbox:{msisdn}", 0, -1)
        messages = []

        for message_id in message_ids:
            raw = redis_client.get(f"sms:{message_id}")
            if raw:
                messages.append(json.loads(raw))

        return jsonify({
            "msisdn": msisdn,
            "count": len(messages),
            "messages": messages
        }), 200

    except Exception as exc:
        logging.exception("Error while reading inbox")
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    start_http_server(SMSC_METRICS_PORT)
    update_pending_gauge()
    app.run(host="0.0.0.0", port=SMSC_HTTP_PORT)
