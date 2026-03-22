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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
