FROM apache/airflow:2.8.4-python3.11

USER root
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
USER airflow

# Install pipeline deps (dbt + psycopg2 + pandas etc) so BashOperator steps can run.
COPY airflow/requirements-airflow.txt /requirements-airflow.txt
RUN pip install --no-cache-dir -r /requirements-airflow.txt
