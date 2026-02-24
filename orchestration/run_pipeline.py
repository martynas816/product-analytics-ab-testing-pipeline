import os
import json
import uuid
import traceback
from datetime import datetime, timezone
from pathlib import Path

import psycopg2

from orchestration.flow import daily_pipeline


def env(name: str, default: str | None = None) -> str:
    v = os.getenv(name, default)
    if v is None:
        raise RuntimeError(f"Missing env var: {name}")
    return v


def connect():
    return psycopg2.connect(
        host=env("POSTGRES_HOST", "localhost"),
        port=int(env("POSTGRES_PORT", "5432")),
        dbname=env("POSTGRES_DB", "analytics"),
        user=env("POSTGRES_USER", "analytics"),
        password=env("POSTGRES_PASSWORD", "analytics"),
    )


def main():
    run_id = str(uuid.uuid4())
    started = datetime.now(timezone.utc)

    conn = connect()
    conn.autocommit = True

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ops.pipeline_runs(run_id, started_at, status)
            VALUES (%s, %s, %s)
            """,
            (run_id, started, "RUNNING"),
        )

    status = "SUCCESS"
    notes = None
    dbt_state = None
    rows_loaded = None
    max_event_ts = None

    try:
        result = daily_pipeline(run_id=run_id)

        rows_loaded = result.get("rows_loaded_from_csv")
        dbt_state = result.get("dbt")

        # Pull max_event_ts for logging
        with conn.cursor() as cur:
            cur.execute("select max(event_ts) from raw.events;")
            max_event_ts = cur.fetchone()[0]

        # Write run_summary.json (artifact)
        out = Path("outputs")
        out.mkdir(exist_ok=True)
        summary_path = out / "run_summary.json"
        summary = {
            "run_id": run_id,
            "started_at": started.isoformat(),
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "rows_loaded_from_csv": rows_loaded,
            "max_event_ts": None if max_event_ts is None else str(max_event_ts),
            "dbt": dbt_state,
            "notes": "See outputs/ab_test_decision.md and outputs/monitoring_report.md",
        }
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Wrote {summary_path}")

    except Exception:
        status = "FAILED"
        notes = traceback.format_exc()[-4000:]
        print(notes)

    ended = datetime.now(timezone.utc)

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE ops.pipeline_runs
            SET ended_at=%s,
                status=%s,
                rows_loaded=%s,
                max_event_ts=%s,
                dbt_state=%s::jsonb,
                notes=%s
            WHERE run_id=%s
            """,
            (ended, status, rows_loaded, max_event_ts, json.dumps(dbt_state) if dbt_state else None, notes, run_id),
        )

    conn.close()

    if status != "SUCCESS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
