import os
from pathlib import Path

import psycopg2


def env(name: str, default: str | None = None) -> str:
    v = os.getenv(name, default)
    if v is None:
        raise RuntimeError(f"Missing env var: {name}")
    return v


def load_csv_to_postgres(csv_path: Path) -> int:
    conn = psycopg2.connect(
        host=env("POSTGRES_HOST", "localhost"),
        port=int(env("POSTGRES_PORT", "5432")),
        dbname=env("POSTGRES_DB", "analytics"),
        user=env("POSTGRES_USER", "analytics"),
        password=env("POSTGRES_PASSWORD", "analytics"),
    )
    conn.autocommit = True

    with conn.cursor() as cur:
        # Ensure table exists (init.sql should create it, but this makes script robust)
        cur.execute(
            """
        CREATE SCHEMA IF NOT EXISTS raw;
        CREATE TABLE IF NOT EXISTS raw.events (
            event_id         uuid PRIMARY KEY,
            event_ts         timestamptz NOT NULL,
            user_id          text NOT NULL,
            session_id       text NOT NULL,
            event_name       text NOT NULL,
            properties       jsonb NOT NULL,
            experiment_key   text,
            variant          text
        );
        """
        )

        # Load to a temp table first (so we can validate + upsert cleanly)
        cur.execute("DROP TABLE IF EXISTS raw._events_load;")
        cur.execute(
            """
        CREATE TABLE raw._events_load (LIKE raw.events INCLUDING ALL);
        """
        )

        with csv_path.open("r", encoding="utf-8") as f:
            cur.copy_expert(
                """
                COPY raw._events_load(event_id, event_ts, user_id, session_id, event_name, properties, experiment_key, variant)
                FROM STDIN WITH (FORMAT csv, HEADER true)
                """,
                f,
            )

        # Insert new rows; ignore duplicates (idempotent demo runs)
        cur.execute(
            """
        INSERT INTO raw.events
        SELECT * FROM raw._events_load
        ON CONFLICT (event_id) DO NOTHING;
        """
        )
        cur.execute("SELECT COUNT(*) FROM raw._events_load;")
        loaded = cur.fetchone()[0]

        cur.execute("DROP TABLE raw._events_load;")

    conn.close()
    return int(loaded)


def main():
    csv_path = Path("data/events.csv")
    if not csv_path.exists():
        raise FileNotFoundError("data/events.csv not found. Run extract/generate_events.py first.")

    n = load_csv_to_postgres(csv_path)
    print(f"Loaded {n:,} rows into raw.events")


if __name__ == "__main__":
    main()
