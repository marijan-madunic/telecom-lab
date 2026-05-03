import requests
import random
import time

AAA_URL = "http://localhost:8080"

# weighted lista za realniji promet
IMSIS = [
    "001010000000001",
    "001010000000002",
    "001010000000003",
    "001010000000004",
    "001010000000005",
    "001010000000006",
    "001010000000007",
    "001010000000008",
    "001010000000999",
    "001010000000666",
]

while True:
    imsi = random.choice(IMSIS)
    url = f"{AAA_URL}/auth/{imsi}"

    try:
        r = requests.get(url, timeout=3)
        print(f"IMSI {imsi} -> {r.status_code} -> {r.text}")
    except Exception as e:
        print(f"IMSI {imsi} -> request failed: {e}")

    time.sleep(random.uniform(0.2, 1.0))
