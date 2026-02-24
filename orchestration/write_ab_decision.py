import os
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import psycopg2


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


def diff_in_proportions_ci(p1, n1, p2, n2, z=1.96):
    se = math.sqrt(p1*(1-p1)/n1 + p2*(1-p2)/n2)
    diff = p2 - p1
    return diff, diff - z*se, diff + z*se


def write_decision() -> Path:
    conn = connect()

    # Primary metric: checkout -> purchase within 24h (from dbt mart)
    q = """
    select
      variant,
      sum(users_started_checkout)::bigint as n_checkout_users,
      sum(users_purchased_24h)::bigint as n_purch_users
    from analytics.mart_conversion_daily
    where variant in ('control','treatment')
    group by 1
    order by 1;
    """
    df = pd.read_sql(q, conn).set_index("variant")

    # Guardrail: average order value
    q_aov = """
    select variant, avg(revenue) as aov, count(*) as orders
    from analytics.fct_orders
    where variant in ('control','treatment')
    group by 1
    order by 1;
    """
    aov = pd.read_sql(q_aov, conn).set_index("variant")

    conn.close()

    if "control" not in df.index or "treatment" not in df.index:
        raise RuntimeError("Not enough data for both variants. Run the pipeline first.")

    n1 = int(df.loc["control", "n_checkout_users"])
    x1 = int(df.loc["control", "n_purch_users"])
    n2 = int(df.loc["treatment", "n_checkout_users"])
    x2 = int(df.loc["treatment", "n_purch_users"])

    p1 = x1 / n1 if n1 else 0.0
    p2 = x2 / n2 if n2 else 0.0

    diff, lo, hi = diff_in_proportions_ci(p1, n1, p2, n2)
    rel = (diff / p1) if p1 > 0 else None

    # Decision rule: ship if CI lower bound > 0 and guardrail not worse by >2%
    control_aov = float(aov.loc["control", "aov"]) if "control" in aov.index else None
    treat_aov = float(aov.loc["treatment", "aov"]) if "treatment" in aov.index else None
    aov_change = None if (control_aov is None or treat_aov is None) else (treat_aov - control_aov) / control_aov

    ship = (lo > 0)
    if aov_change is not None and aov_change < -0.02:
        ship = False

    out = Path("outputs")
    out.mkdir(exist_ok=True)
    p = out / "ab_test_decision.md"

    lines = []
    lines.append("# A/B test decision — `new_checkout`\n")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}\n")
    lines.append("\n## Primary metric\n")
    lines.append("**Metric:** checkout → purchase conversion within **24h**\n\n")
    lines.append("| variant | checkout users | purchasers | conversion |\n")
    lines.append("|---|---:|---:|---:|\n")
    lines.append(f"| control | {n1:,} | {x1:,} | {p1:.4f} |\n")
    lines.append(f"| treatment | {n2:,} | {x2:,} | {p2:.4f} |\n")

    lines.append("\n## Effect size\n")
    lines.append(f"- Uplift (abs): **{diff:.4f}**\n")
    if rel is not None:
        lines.append(f"- Uplift (rel): **{rel*100:.2f}%**\n")
    lines.append(f"- 95% CI (abs): **[{lo:.4f}, {hi:.4f}]**\n")

    lines.append("\n## Guardrail\n")
    if aov_change is None:
        lines.append("- AOV guardrail: not available\n")
    else:
        lines.append(f"- AOV control: `{control_aov:.2f}`\n")
        lines.append(f"- AOV treatment: `{treat_aov:.2f}`\n")
        lines.append(f"- AOV change: `{aov_change*100:.2f}%`\n")

    lines.append("\n## Decision\n")
    if ship:
        lines.append(" **SHIP** — uplift CI is above 0 and guardrail is acceptable.\n")
    else:
        lines.append(" **DO NOT SHIP YET** — either CI includes 0 or guardrail regressed beyond tolerance.\n")

    lines.append("\n## Notes\n")
    lines.append("- This decision is computed from tracked events defined in `spec/event_tracking.md`.\n")
    lines.append("- For a deeper dive, see `experiment/ab_test_analysis.ipynb`.\n")

    p.write_text("".join(lines), encoding="utf-8")
    return p
