FROM python:3.11-slim

WORKDIR /app

# System deps for psycopg2 + git (dbt deps if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# dbt looks for profiles.yml; we keep it in /app/dbt
ENV DBT_PROFILES_DIR=/app/dbt

CMD ["python", "orchestration/run_pipeline.py"]
