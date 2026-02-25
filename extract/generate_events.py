import os
import json
import uuid
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd


EVENTS = [
    "app_open",
    "signup_started",
    "signup_completed",
    "product_view",
    "add_to_cart",
    "checkout_started",
    "purchase_completed",
]

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def generate_events(
    n_users: int = 6000,
    n_days: int = 60,
    seed: int = 42,
    experiment_key: str = "new_checkout",
) -> pd.DataFrame:
    random.seed(seed)

    end = _now_utc()
    # Keep generated timestamps safely behind database NOW() to avoid clock skew and long-session spillover.
    hard_end = end - timedelta(minutes=10)
    start = hard_end - timedelta(days=n_days)
    max_event_lag = timedelta(hours=2, minutes=30)
    latest_session_start = hard_end - max_event_lag

    # Assign experiment variant at user level
    user_ids = [f"u_{i:06d}" for i in range(1, n_users + 1)]
    variants = {u: ("treatment" if random.random() < 0.5 else "control") for u in user_ids}

    rows = []

    def add_event(event_ts, user_id, session_id, event_name, props, exp_key=experiment_key, variant=None):
        event_ts = min(event_ts, hard_end)
        rows.append({
            "event_id": str(uuid.uuid4()),
            "event_ts": event_ts.isoformat(),
            "user_id": user_id,
            "session_id": session_id,
            "event_name": event_name,
            "properties": json.dumps(props, separators=(",", ":")),
            "experiment_key": exp_key,
            "variant": variant
        })

    # Global product catalog
    product_ids = [f"p_{i:05d}" for i in range(1, 2001)]
    categories = ["electronics", "home", "beauty", "sports", "fashion"]

    for u in user_ids:
        v = variants[u]

        # User activity level: 1..8 sessions across the whole window
        n_sessions = 1 + int(random.random() * 8)
        first_seen = start + timedelta(seconds=random.randint(0, int((end-start).total_seconds())))

        for s in range(n_sessions):
            # Session start time jittered forward from first_seen
            session_ts = first_seen + timedelta(days=random.random() * (n_days - 1), minutes=random.random() * 1440)
            if session_ts > latest_session_start:
                session_ts = latest_session_start - timedelta(minutes=random.random() * 60)

            session_id = f"s_{uuid.uuid4().hex[:10]}"

            # app_open always happens
            add_event(session_ts, u, session_id, "app_open", {
                "platform": random.choice(["web", "ios", "android"]),
                "referrer": random.choice(["direct", "google", "instagram", "tiktok", "email"]),
            }, variant=v)

            # signup funnel happens mostly in first session(s)
            did_signup = False
            if s == 0 and random.random() < 0.70:
                add_event(session_ts + timedelta(seconds=random.randint(10, 120)), u, session_id, "signup_started", {
                    "signup_method": random.choice(["email", "google", "apple"])
                }, variant=v)

                # completion probability
                if random.random() < 0.80:
                    did_signup = True
                    add_event(session_ts + timedelta(seconds=random.randint(150, 600)), u, session_id, "signup_completed", {
                        "signup_method": random.choice(["email", "google", "apple"]),
                        "country": random.choice(["LT", "LV", "EE", "PL", "DE", "UK", "SE"])
                    }, variant=v)

            # browse products
            n_views = random.randint(1, 6)
            t = session_ts + timedelta(minutes=1)
            for _ in range(n_views):
                pid = random.choice(product_ids)
                price = round(random.uniform(5, 250), 2)
                add_event(t, u, session_id, "product_view", {
                    "product_id": pid,
                    "category": random.choice(categories),
                    "price": price
                }, variant=v)
                t += timedelta(seconds=random.randint(20, 120))

                # some add to cart
                if random.random() < 0.25:
                    qty = random.randint(1, 3)
                    add_event(t, u, session_id, "add_to_cart", {
                        "product_id": pid,
                        "quantity": qty,
                        "price": price
                    }, variant=v)
                    t += timedelta(seconds=random.randint(10, 90))

            # checkout attempt if cart exists
            # (approx proxy: chance increases with views)
            base_checkout_p = 0.12 + 0.02 * n_views
            if random.random() < min(base_checkout_p, 0.40):
                cart_value = round(random.uniform(15, 350), 2)
                items = random.randint(1, 5)
                add_event(t, u, session_id, "checkout_started", {
                    "cart_value": cart_value,
                    "items": items
                }, variant=v)
                t += timedelta(seconds=random.randint(20, 90))

                # purchase probability depends on variant (treatment uplift)
                # control: 22% given checkout_started
                # treatment: +2.5pp absolute uplift
                purchase_p = 0.22 + (0.025 if v == "treatment" else 0.0)

                if random.random() < purchase_p:
                    order_id = f"o_{uuid.uuid4().hex[:12]}"
                    revenue = round(cart_value * random.uniform(0.95, 1.10), 2)

                    add_event(t, u, session_id, "purchase_completed", {
                        "order_id": order_id,
                        "revenue": revenue,
                        "currency": "EUR",
                        "items": items
                    }, variant=v)

    df = pd.DataFrame(rows)
    # Parse to datetime for sorting, but keep ISO strings for CSV portability
    df["_ts"] = pd.to_datetime(df["event_ts"], utc=True)
    df = df.sort_values("_ts").drop(columns=["_ts"]).reset_index(drop=True)

    return df


def main():
    n_users = int(os.getenv("SYNTH_USERS", "6000"))
    n_days = int(os.getenv("SYNTH_DAYS", "60"))
    seed = int(os.getenv("RANDOM_SEED", "42"))

    out_dir = Path("data")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "events.csv"

    df = generate_events(n_users=n_users, n_days=n_days, seed=seed)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df):,} events to {out_path}")


if __name__ == "__main__":
    main()
