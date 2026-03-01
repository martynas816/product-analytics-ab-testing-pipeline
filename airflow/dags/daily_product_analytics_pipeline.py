from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
import pendulum

# A demo-friendly DAG that orchestrates the same steps as the Prefect flow.
# - generate events
# - load events
# - dbt build (models + tests)
# - monitoring checks
# - A/B decision artifact

LOCAL_TZ = pendulum.timezone("Europe/Vilnius")


def bash(task_id: str, cmd: str, env: dict | None = None) -> BashOperator:
    return BashOperator(
        task_id=task_id,
        bash_command=f"cd /opt/airflow/repo && {cmd}",
        env=env,
    )


with DAG(
    dag_id="daily_product_analytics_pipeline",
    description="Product analytics ELT pipeline (Airflow version) — raw -> dbt -> monitors -> decision",
    start_date=datetime(2026, 1, 1, tzinfo=LOCAL_TZ),
    schedule=None,  # manual trigger for demo
    catchup=False,
    tags=["portfolio", "product_analytics", "dbt", "postgres"],
) as dag:

    # Use Airflow run_id to tag monitoring outputs (surfaced in monitoring_report.md)
    run_id = "{{ run_id }}"

    generate_events = bash(
        "generate_events",
        "python extract/generate_events.py",
    )

    load_events = bash(
        "load_events",
        "python extract/load_events.py",
    )

    dbt_build = bash(
        "dbt_build",
        "dbt build --project-dir /opt/airflow/repo/dbt --profiles-dir /opt/airflow/repo/dbt",
    )

    run_monitors = bash(
        "run_monitors",
        f"PIPELINE_RUN_ID={run_id} python monitoring/run_monitors.py",
    )

    write_decision = bash(
        "write_ab_decision",
        "python orchestration/write_ab_decision.py",
    )

    generate_events >> load_events >> dbt_build >> run_monitors >> write_decision
