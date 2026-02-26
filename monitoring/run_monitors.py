import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypedDict

import pandas as pd

FRESHNESS_THRESHOLD_HOURS = float(os.getenv("FRESHNESS_THRESHOLD_HOURS", "24"))
Z_THRESHOLD = float(os.getenv("ANOMALY_Z_THRESHOLD", "3.0"))

class MonitoringReport(TypedDict):
    freshness: dict[str, Any]
    anomaly: list[dict[str, Any]]
    alerts: list[dict[str, Any]]


def env(name: str, default: str | None = None) -> str:
    v = os.getenv(name, default)
    if v is None:
        raise RuntimeError(f"Missing env var: {name}")
    return v


def connect():
    import psycopg2

    return psycopg2.connect(
        host=env("POSTGRES_HOST", "localhost"),
        port=int(env("POSTGRES_PORT", "5432")),
        dbname=env("POSTGRES_DB", "analytics"),
        user=env("POSTGRES_USER", "analytics"),
        password=env("POSTGRES_PASSWORD", "analytics"),
    )

def insert_alert(cur, run_id, alert_type, severity, message, details):
    cur.execute(
        """
        INSERT INTO ops.monitoring_alerts(alert_id, run_id, created_at, alert_type, severity, message, details)
        VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)
        """,
        (
            str(uuid.uuid4()),
            str(run_id),
            datetime.now(UTC),
            alert_type,
            severity,
            message,
            json.dumps(details),
        ),
    )

def format_freshness_alert_message(lag_hours: float | None, threshold_hours: float) -> str:
    if lag_hours is None:
        return f"Freshness FAIL: no events found in raw.events (threshold {threshold_hours}h)"
    return f"Freshness FAIL: latest event is {lag_hours:.1f}h old (threshold {threshold_hours}h)"

def run_monitors(run_id: str) -> MonitoringReport:
    freshness_q = (
        "select max(event_ts) as max_event_ts, now() - max(event_ts) as lag from raw.events;"
    )

    anomaly_q = """
    with daily as (
      select event_day::date as day, variant, users_started_checkout, checkout_to_purchase_rate_24h as rate
      from analytics.mart_conversion_daily
      where event_day >= now() - interval '45 days'
        and variant in ('control','treatment')
    ),
    latest_day as (select max(day) as day from daily),
    baseline as (
      select d.variant, avg(d.rate) as mean_rate, stddev_pop(d.rate) as std_rate
      from daily d
      join latest_day l on d.day < l.day
      where d.users_started_checkout >= 200
      group by 1
    ),
    latest as (
      select d.variant, d.day, d.users_started_checkout, d.rate
      from daily d
      join latest_day l on d.day = l.day
    )
    select l.variant, l.day, l.users_started_checkout, l.rate, b.mean_rate, b.std_rate,
           case when b.std_rate is null or b.std_rate = 0 then null else (l.rate - b.mean_rate)/b.std_rate end as z_score
    from latest l
    left join baseline b on b.variant = l.variant
    order by l.variant;
    """

    conn = connect()
    conn.autocommit = True

    report: MonitoringReport = {"freshness": {}, "anomaly": [], "alerts": []}

    with conn.cursor() as cur:
        # Freshness
        df_f = pd.read_sql(freshness_q, conn)
        max_ts = df_f.loc[0, "max_event_ts"]
        lag = df_f.loc[0, "lag"]
        lag_hours = lag.total_seconds() / 3600 if lag is not None else None

        freshness: dict[str, Any] = {
            "max_event_ts": None if max_ts is None else str(max_ts),
            "lag_hours": lag_hours,
            "threshold_hours": FRESHNESS_THRESHOLD_HOURS,
        }
        freshness["status"] = (
            "PASS" if (lag_hours is not None and lag_hours <= FRESHNESS_THRESHOLD_HOURS) else "FAIL"
        )
        report["freshness"] = freshness

        if freshness["status"] == "FAIL":
            msg = format_freshness_alert_message(lag_hours, FRESHNESS_THRESHOLD_HOURS)
            insert_alert(cur, run_id, "freshness", "high", msg, freshness)
            report["alerts"].append({"type": "freshness", "severity": "high", "message": msg})

        # Anomaly
        df_a = pd.read_sql(anomaly_q, conn)
        for _, r in df_a.iterrows():
            item: dict[str, Any] = {}
            for k, v in r.to_dict().items():
                if pd.isna(v):
                    item[k] = None
                elif hasattr(v, "isoformat"):
                    item[k] = v.isoformat()
                else:
                    item[k] = float(v) if isinstance(v, int | float) else v
            report["anomaly"].append(item)

            z = r.get("z_score")
            starters = r.get("users_started_checkout") or 0
            if (
                z is not None
                and not pd.isna(z)
                and abs(float(z)) >= Z_THRESHOLD
                and starters >= 200
            ):
                sev = "medium" if abs(float(z)) < 4 else "high"
                msg = f"Anomaly {sev.upper()}: {r['variant']} conversion z={float(z):.2f} on {r['day']}"
                insert_alert(
                    cur, run_id, "conversion_anomaly", sev, msg, item | {"z_threshold": Z_THRESHOLD}
                )
                report["alerts"].append(
                    {"type": "conversion_anomaly", "severity": sev, "message": msg}
                )

    conn.close()
    return report

def write_markdown(report: MonitoringReport) -> Path:
    out = Path("outputs")
    out.mkdir(exist_ok=True)
    p = out / "monitoring_report.md"

    f = report["freshness"]

    lines = []
    lines.append("# Monitoring report\n")
    lines.append(f"Generated: {datetime.now(UTC).isoformat()}\n")
    lines.append("\n## Freshness\n")
    lines.append(f"- Max event timestamp: `{f.get('max_event_ts')}`\n")
    lines.append(
        f"- Lag (hours): `{float(f.get('lag_hours') or 0):.2f}` (threshold `{f.get('threshold_hours')}`)\n"
    )
    lines.append(f"- Status: **{f.get('status')}**\n")

    lines.append("\n## Conversion anomaly (z-score)\n")
    lines.append("| variant | day | starters | rate | mean | std | z |\n")
    lines.append("|---|---:|---:|---:|---:|---:|---:|\n")
    for a in report["anomaly"]:
        z = a.get("z_score")
        z_str = "" if z is None else f"{float(z):.2f}"
        lines.append(
            f"| {a.get('variant')} | {a.get('day')} | {int(float(a.get('users_started_checkout') or 0))} | "
            f"{float(a.get('rate') or 0):.4f} | {float(a.get('mean_rate') or 0):.4f} | {float(a.get('std_rate') or 0):.4f} | {z_str} |\n"
        )

    lines.append("\n## Alerts\n")
    if report["alerts"]:
        for al in report["alerts"]:
            lines.append(f"- **{al['severity']}** `{al['type']}`: {al['message']}\n")
    else:
        lines.append("- None\n")

    p.write_text("".join(lines), encoding="utf-8")
    return p

if __name__ == "__main__":
    run_id = env("PIPELINE_RUN_ID", None) or str(uuid.uuid4())
    report = run_monitors(run_id)
    path = write_markdown(report)
    print(f"Wrote {path}")
