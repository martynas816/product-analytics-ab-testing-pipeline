FROM python:3.11-slim

WORKDIR /app

# App + dbt config
ENV PYTHONPATH=/app \
    DBT_PROFILES_DIR=/app/dbt \
    PYTHONUNBUFFERED=1

# System deps:
# - gcc + libpq-dev: psycopg2 build deps (even if using psycopg2-binary, libpq is useful)
# - git: dbt can pull packages via git (and dbt checks for it)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    git \
  && rm -rf /var/lib/apt/lists/*

# Python deps (constraints pins Prefect-compatible versions)
COPY requirements.txt constraints.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r /app/requirements.txt -c /app/constraints.txt

# Project code
COPY . /app

CMD ["python", "orchestration/run_pipeline.py"]
