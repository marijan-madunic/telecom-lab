import random
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "telecom",
    "user": "postgres",
    "password": "postgres"
}

NUM_USERS = 1000

PLANS = [
    {"id": 1, "name": "basic", "limit": 5000},
    {"id": 2, "name": "premium", "limit": 20000}
]


def generate_imsi(i: int) -> str:
    return f"00101{i:010d}"


def generate_msisdn(i: int) -> str:
    return f"38591{i:07d}"


def pick_plan() -> dict:
    return random.choice(PLANS)


def main() -> None:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print("Cleaning old subscriber data...")

    cur.execute("DELETE FROM balances;")
    cur.execute("DELETE FROM subscriber_profiles;")
    cur.execute("DELETE FROM subscribers;")
    conn.commit()

    subscribers = []
    profiles = []
    balances = []

    for i in range(NUM_USERS):
        imsi = generate_imsi(i)
        msisdn = generate_msisdn(i)
        plan = pick_plan()

        status = random.choices(
            ["ACTIVE", "SUSPENDED"],
            weights=[0.9, 0.1]
        )[0]

        subscribers.append((
            imsi,
            msisdn,
            status,
            plan["id"],
            datetime.now()
        ))

    execute_batch(cur, """
        INSERT INTO subscribers (imsi, msisdn, status, plan_id, created_at)
        VALUES (%s, %s, %s, %s, %s)
    """, subscribers)

    conn.commit()

    cur.execute("SELECT id, plan_id FROM subscribers ORDER BY id")
    rows = cur.fetchall()

    for sub_id, plan_id in rows:
        profiles.append((
            sub_id,
            random.choice([True, False]),
            True,
            random.randint(1, 5)
        ))

        plan = next(p for p in PLANS if p["id"] == plan_id)
        balances.append((
            sub_id,
            random.randint(int(plan["limit"] * 0.5), plan["limit"]),
            datetime.now()
        ))

    execute_batch(cur, """
        INSERT INTO subscriber_profiles (
            subscriber_id,
            access_restriction,
            roaming_enabled,
            max_sessions
        )
        VALUES (%s, %s, %s, %s)
    """, profiles)

    execute_batch(cur, """
        INSERT INTO balances (
            subscriber_id,
            remaining_data_mb,
            last_updated
        )
        VALUES (%s, %s, %s)
    """, balances)

    conn.commit()

    print(f"Seeded {NUM_USERS} subscribers successfully.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
