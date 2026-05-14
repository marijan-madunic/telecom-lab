import logging
from flask import Flask, jsonify, request

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Policies po planu
POLICIES = {
    "gold": "premium",
    "silver": "standard",
    "bronze": "basic"
}

# Roaming downgrade map
ROAMING_DOWNGRADE = {
    "premium": "standard",
    "standard": "basic",
    "basic": "basic"
}

@app.route("/health")
def health():
    return {"status": "ok"}, 200

@app.route("/")
def home():
    return jsonify({"status": "PCRF running"})

@app.route("/policy/<plan>", methods=["GET"])
def policy(plan):
    try:
        # query param: ?roaming=true
        roaming = request.args.get("roaming", "false").lower() == "true"

        base_policy = POLICIES.get(plan, "basic")
        logger.info(f"Plan received: {plan} → base_policy: {base_policy}")

        if roaming:
            final_policy = ROAMING_DOWNGRADE.get(base_policy, "basic")
            logger.info(f"Roaming user → downgrade {base_policy} → {final_policy}")
        else:
            final_policy = base_policy
            logger.info("Non-roaming user → no downgrade")

        return jsonify({
            "plan": plan,
            "policy": final_policy,
            "roaming": roaming
        })

    except Exception as e:
        logger.error(f"ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/diameter/ccr", methods=["POST"])
def diameter_ccr():
    try:
        ccr = request.json

        imsi = ccr.get("imsi")
        plan = ccr.get("qos_class", "bronze")
        session_id = ccr.get("session_id")
        requested_bandwidth = ccr.get("requested_bandwidth", "10Mbps")

        logger.info(f"Diameter CCR received: IMSI={imsi}, plan={plan}, session={session_id}")

        cca = {
            "diameter_command": "CCA",
            "session_id": session_id,
            "result_code": 2001,
            "policy_rule": f"internet-{plan}",
            "granted_bandwidth": requested_bandwidth,
            "avps": {
                "Session-Id": session_id,
                "Result-Code": 2001,
                "Charging-Rule-Name": f"internet-{plan}",
                "QoS-Class-Identifier": plan,
                "APN-Aggregate-Max-Bitrate": requested_bandwidth
            }
        }

        return jsonify(cca), 200

    except Exception as e:
        logger.error(f"Diameter CCR error: {str(e)}")
        return jsonify({
            "diameter_command": "CCA",
            "result_code": 5005,
            "error": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
