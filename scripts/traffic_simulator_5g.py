import requests
import random
import time

AMF_URL = "http://localhost:8086"

IMSIS = [
    "001010000000001",
    "001010000000002",
    "001010000000003",
    "001010000000004",
    "001010000000005",
    "001010000000006",
    "001010000000007",
    "001010000000008",
    "001010000000999",  # blocked
    "001010000000666",  # blocked
]

while True:
    imsi = random.choice(IMSIS)

    try:
        # REGISTER
        reg = requests.post(
            f"{AMF_URL}/register",
            json={"imsi": imsi},
            timeout=10
        )

        # PDU SESSION
        pdu = requests.post(
            f"{AMF_URL}/pdu-session",
            json={"imsi": imsi, "dnn": "internet"},
            timeout=15
        )

        print(
            f"IMSI {imsi} | "
            f"REG {reg.status_code} | "
            f"PDU {pdu.status_code}"
        )

    except Exception as e:
        print(f"IMSI {imsi} -> request failed: {e}")

    time.sleep(random.uniform(0.2, 1.0))
