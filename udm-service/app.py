import os
import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "host.minikube.internal"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "telecom"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def get_subscriber_data(imsi):
    query = """
        SELECT
            s.imsi,
            s.msisdn,
            s.status,
            p.name AS plan_name,
            p.data_limit_mb,
            p.qos_profile,
            sp.access_restriction,
            sp.roaming_enabled,
            sp.max_sessions
        FROM subscribers s
        JOIN plans p ON s.plan_id = p.id
        JOIN subscriber_profiles sp ON sp.subscriber_id = s.id
        WHERE s.imsi = %s;
    """

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(query, (imsi,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "imsi": row[0],
        "msisdn": row[1],
        "status": row[2],
        "profile": {
            "plan": row[3],
            "data_limit_mb": row[4],
            "qos_profile": row[5],
            "access_restriction": row[6],
            "roaming_enabled": row[7],
            "max_sessions": row[8],
        },
    }


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/subscriber/<imsi>", methods=["GET"])
def subscriber(imsi):
    data = get_subscriber_data(imsi)

    if not data:
        return jsonify({"error": "subscriber not found"}), 404

    return jsonify(data), 200


@app.route("/auth/<imsi>", methods=["GET"])
def auth_data(imsi):
    data = get_subscriber_data(imsi)

    if not data:
        return jsonify({"error": "subscriber not found"}), 404

    if data["status"] != "ACTIVE":
        return jsonify({
            "imsi": imsi,
            "auth_allowed": False,
            "reason": f"subscriber status is {data['status']}"
        }), 403

    if data["profile"]["access_restriction"]:
        return jsonify({
            "imsi": imsi,
            "auth_allowed": False,
            "reason": "access restriction enabled"
        }), 403

    return jsonify({
        "imsi": imsi,
        "auth_allowed": True,
        "status": data["status"]
    }), 200


@app.route("/policy/<imsi>", methods=["GET"])
def policy_data(imsi):
    data = get_subscriber_data(imsi)

    if not data:
        return jsonify({"error": "subscriber not found"}), 404

    return jsonify({
        "imsi": data["imsi"],
        "plan": data["profile"]["plan"],
        "qos_profile": data["profile"]["qos_profile"],
        "roaming_enabled": data["profile"]["roaming_enabled"],
        "max_sessions": data["profile"]["max_sessions"],
        "access_restriction": data["profile"]["access_restriction"]
    }), 200


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "UDM service running with PostgreSQL backend"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082)
