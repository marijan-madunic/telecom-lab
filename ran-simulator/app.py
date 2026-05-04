import os
import time
import random
import threading
import requests

from flask import Flask, jsonify
from prometheus_client import start_http_server, Counter, Gauge

app = Flask(__name__)

AMF_URL = os.getenv("AMF_URL", "http://amf-service:8086")
METRICS_PORT = int(os.getenv("METRICS_PORT", "8007"))
INTERVAL_SECONDS = int(os.getenv("INTERVAL_SECONDS", "5"))
UDM_URL = os.getenv("UDM_URL", "http://udm-service:8082")
UE_POOL_SIZE = int(os.getenv("UE_POOL_SIZE", "10"))

CELLS = {
    "cell-A": {"connected_ues": set(), "prb_usage": 25},
    "cell-B": {"connected_ues": set(), "prb_usage": 45},
    "cell-C": {"connected_ues": set(), "prb_usage": 65},
}

IMSIS = []

ue_location = {}

ran_events_total = Counter(
    "ran_events_total",
    "Total RAN simulator events",
    ["event_type"]
)

ran_handover_requests_total = Counter(
    "ran_handover_requests_total",
    "Total handover requests sent from RAN simulator to AMF"
)

ran_handover_failures_total = Counter(
    "ran_handover_failures_total",
    "Total failed handover requests from RAN simulator to AMF"
)

ran_cell_connected_ues = Gauge(
    "ran_cell_connected_ues",
    "Number of connected UEs per simulated cell",
    ["cell"]
)

ran_cell_prb_usage = Gauge(
    "ran_cell_prb_usage",
    "Simulated PRB usage per cell",
    ["cell"]
)


def update_metrics():
    for cell_name, cell in CELLS.items():
        ran_cell_connected_ues.labels(cell=cell_name).set(len(cell["connected_ues"]))
        ran_cell_prb_usage.labels(cell=cell_name).set(cell["prb_usage"])


def pick_best_cell(current_cell):
    candidates = [c for c in CELLS.keys() if c != current_cell]
    return min(candidates, key=lambda c: CELLS[c]["prb_usage"])

def load_eligible_imsis():
    global IMSIS

    try:
        response = requests.get(
            f"{UDM_URL}/subscribers/eligible",
            timeout=10
        )

        if response.status_code != 200:
            print(f"[RAN] Failed to fetch eligible IMSIs from UDM: HTTP {response.status_code}")
            IMSIS = []
            return

        data = response.json()
        IMSIS = data.get("imsis", [])[:UE_POOL_SIZE]

        print(f"[RAN] Loaded {len(IMSIS)} eligible IMSIs from UDM: {IMSIS}")

    except Exception as e:
        print(f"[RAN] Failed to load eligible IMSIs from UDM: {e}")
        IMSIS = []

def register_ue(imsi):
    cell = random.choice(list(CELLS.keys()))

    try:
        response = requests.post(
            f"{AMF_URL}/register",
            json={"imsi": imsi},
            timeout=10
        )

        if response.status_code == 200:
            ue_location[imsi] = cell
            CELLS[cell]["connected_ues"].add(imsi)

            ran_events_total.labels(event_type="registration").inc()
            print(f"[RAN] UE {imsi} registered via {cell}")
        else:
            print(f"[RAN] Registration rejected for {imsi}: HTTP {response.status_code}")

    except Exception as e:
        print(f"[RAN] Registration failed for {imsi}: {e}")


def trigger_handover(imsi):
    from_cell = ue_location.get(imsi)

    if not from_cell:
        register_ue(imsi)
        return

    to_cell = pick_best_cell(from_cell)

    payload = {
        "imsi": imsi,
        "from_cell": from_cell,
        "to_cell": to_cell,
        "reason": "better_signal_or_lower_load"
    }

    try:
        response = requests.post(f"{AMF_URL}/handover", json=payload, timeout=5)

        if response.status_code in [200, 201]:
            CELLS[from_cell]["connected_ues"].discard(imsi)
            CELLS[to_cell]["connected_ues"].add(imsi)
            ue_location[imsi] = to_cell

            ran_handover_requests_total.inc()
            ran_events_total.labels(event_type="handover").inc()

            print(f"[RAN] HO success IMSI={imsi}: {from_cell} -> {to_cell}")
        else:
            ran_handover_failures_total.inc()
            print(f"[RAN] HO rejected IMSI={imsi}: HTTP {response.status_code}")

    except Exception as e:
        ran_handover_failures_total.inc()
        print(f"[RAN] HO failed IMSI={imsi}: {e}")


def simulate_cell_load():
    for cell in CELLS.values():
        delta = random.randint(-10, 15)
        cell["prb_usage"] = max(5, min(95, cell["prb_usage"] + delta))


def simulation_loop():
    print("[RAN] Starting RAN/gNB simulator loop")

    load_eligible_imsis()

    if not IMSIS:
        print("[RAN] No eligible IMSIs available. Simulator stopped.")
        return

    for imsi in IMSIS:
        register_ue(imsi)

    while True:
        simulate_cell_load()

        imsi = random.choice(IMSIS)
        current_cell = ue_location.get(imsi)

        if current_cell and CELLS[current_cell]["prb_usage"] > 70:
            trigger_handover(imsi)
        elif random.random() < 0.35:
            trigger_handover(imsi)
        else:
            ran_events_total.labels(event_type="measurement_report").inc()
            print(f"[RAN] Measurement report IMSI={imsi}, cell={current_cell}")

        update_metrics()
        time.sleep(INTERVAL_SECONDS)


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "ran-simulator"
    })


@app.route("/cells")
def cells():
    return jsonify({
        cell_name: {
            "connected_ues": len(cell["connected_ues"]),
            "prb_usage": cell["prb_usage"]
        }
        for cell_name, cell in CELLS.items()
    })


@app.route("/ues")
def ues():
    return jsonify(ue_location)


if __name__ == "__main__":
    start_http_server(METRICS_PORT)

    thread = threading.Thread(target=simulation_loop, daemon=True)
    thread.start()

    app.run(host="0.0.0.0", port=8087)
