import os
import json
import redis
import requests
import logging
from flask import Flask, jsonify

app = Flask(__name__)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
UDM_URL = os.environ.get("UDM_URL", "http://udm-service:8082")
PCRF_URL = os.environ.get("PCRF_URL", "http://pcrf-service:8081")
OCS_URL = os.environ.get("OCS_URL", "http://ocs-service:8083")

CACHE_TTL = 60

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

BLACKLIST = {"001010000000999", "001010000000666"}

DOWNGRADE = {
    "gold": "silver",
    "silver": "bronze",
    "bronze": "bronze"
}

@app.route("/health")
def health():
    return {"status": "ok"}, 200

@app.route("/auth/<imsi>", methods=["GET"])
def auth(imsi):
    try:
        if imsi in BLACKLIST:
            logger.warning(f"BLOCKED IMSI {imsi}")
            return jsonify({"imsi": imsi, "auth": "denied", "reason": "blacklisted"}), 403

        cache_key = f"imsi:{imsi}"

        # 🔹 Cache (bez balance!)
        cached = redis_client.get(cache_key)
        if cached:
            logger.info(f"Cache HIT for {imsi}")
            data = json.loads(cached)
            source = "cache"
        else:
            logger.info(f"Cache MISS for {imsi} → calling UDM")

            # 🔹 UDM
            response = requests.get(f"{UDM_URL}/subscriber/{imsi}", timeout=3)

            if response.status_code != 200:
                data = {"imsi": imsi, "plan": "bronze"}
                is_roaming = False
            else:
                data = response.json()
                data["plan"] = data.get("plan", "bronze")
                is_roaming = data.get("is_roaming", False)

            # 🔹 Roaming downgrade
            if is_roaming:
                old_plan = data["plan"]
                data["plan"] = DOWNGRADE.get(data["plan"], "bronze")
                logger.info(f"Roaming IMSI {imsi}: {old_plan} → {data['plan']}")

            # 🔹 PCRF
            try:
                logger.info(f"Calling PCRF: {PCRF_URL}/policy/{data['plan']} roaming={is_roaming}")

                prcf_resp = requests.get(f"{PCRF_URL}/policy/{data['plan']}", params={"roaming": str(is_roaming).lower()}, timeout=2
                )

                logger.info(f"PCRF status: {prcf_resp.status_code}")
                logger.info(f"PCRF response: {prcf_resp.text}")

                if prcf_resp.status_code == 200:
                    data["policy"] = prcf_resp.json().get("policy", "default")
                else:
                    data["policy"] = "default"

            except Exception as e:
                logger.warning(f"PCRF request failed: {e}")
                data["policy"] = "default"

            # 🔹 spremi u cache (bez balance!)
            cache_copy = data.copy()
            cache_copy.pop("balance", None)
            redis_client.setex(cache_key, CACHE_TTL, json.dumps(cache_copy))

            source = "udm"

        # 🔥 OCS UVIJEK ide (izvan cache-a!)
        try:
            logger.info(f"Calling OCS for {imsi}")
            ocs_resp = requests.get(f"{OCS_URL}/check/{imsi}", timeout=2)

            if ocs_resp.status_code == 200:
                ocs_data = ocs_resp.json()

                if not ocs_data.get("allowed", False):
                    logger.warning(f"No balance for {imsi}")
                    return jsonify({
                        "imsi": imsi,
                        "auth": "denied",
                        "reason": "no balance",
                        "balance": ocs_data.get("balance", 0)
                    }), 403

                data["balance"] = ocs_data.get("balance", 0)
            else:
                data["balance"] = 0

        except Exception as e:
            logger.warning(f"OCS request failed: {e}")
            data["balance"] = 0

        data["auth"] = "granted"
        data["source"] = source

        return jsonify(data)

    except Exception as e:
        logger.error(f"AAA ERROR: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "AAA running"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
