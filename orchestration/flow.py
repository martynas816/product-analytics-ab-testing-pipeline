import os
import subprocess
from pathlib import Path

import psycopg2
from prefect import flow, task


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


@task
def generate_events():
    subprocess.run(["python", "extract/generate_events.py"], check=True)


@task
def load_events() -> int:
    # returns rows loaded (from the CSV file, not necessarily inserted if re-run)
    proc = subprocess.run(
        ["python", "extract/load_events.py"], check=True, capture_output=True, text=True
    )
    # naive parse
    out = (proc.stdout or "") + (proc.stderr or "")
    # "Loaded 123 rows into raw.events"
    n = 0
    for token in out.replace(",", " ").split():
        if token.isdigit():
            n = int(token)
            break
    return n


@task
def dbt_build() -> dict:
    """Run `dbt build` and surface logs on failure."""

    project_dir = "/app/dbt"
    profiles_dir = "/app/dbt"
    cmd = ["dbt", "build", "--project-dir", project_dir, "--profiles-dir", profiles_dir]

    proc = subprocess.run(cmd, capture_output=True, text=True)

    state = {
        "command": " ".join(cmd),
        "stdout_tail": (proc.stdout or "")[-4000:],
        "stderr_tail": (proc.stderr or "")[-4000:],
        "returncode": proc.returncode,
    }

    if proc.returncode != 0:
        # Raise with tail logs so Docker / Prefect logs show the real dbt error.
        raise RuntimeError(
            "dbt build failed\n"
            f"command: {state['command']}\n"
            f"returncode: {state['returncode']}\n"
            "--- dbt stderr (tail) ---\n"
            f"{state['stderr_tail']}\n"
            "--- dbt stdout (tail) ---\n"
            f"{state['stdout_tail']}\n"
        )

    return state


@task
def run_monitors(run_id: str) -> dict:
    envs = os.environ.copy()
    envs["PIPELINE_RUN_ID"] = run_id
    proc = subprocess.run(
        ["python", "monitoring/run_monitors.py"],
        check=True,
        capture_output=True,
        text=True,
        env=envs,
    )
    return {
        "stdout_tail": (proc.stdout or "")[-2000:],
        "stderr_tail": (proc.stderr or "")[-2000:],
        "returncode": proc.returncode,
    }


@task
def write_ab_test_decision() -> Path:
    from orchestration.write_ab_decision import write_decision

    return write_decision()


@flow(name="daily_product_analytics_pipeline")
def daily_pipeline(run_id: str) -> dict:
    generate_events()
    rows_loaded = load_events()
    dbt_state = dbt_build()
    monitors_state = run_monitors(run_id)
    decision_path = write_ab_test_decision()

    return {
        "run_id": run_id,
        "rows_loaded_from_csv": rows_loaded,
        "dbt": dbt_state,
        "monitors": monitors_state,
        "ab_decision_path": str(decision_path),
    }
