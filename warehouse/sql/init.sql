-- Schemas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS ops;

-- Raw events table (append-only)
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

CREATE INDEX IF NOT EXISTS idx_events_ts ON raw.events (event_ts);
CREATE INDEX IF NOT EXISTS idx_events_user ON raw.events (user_id);
CREATE INDEX IF NOT EXISTS idx_events_name ON raw.events (event_name);

-- Pipeline run logs (operational visibility)
CREATE TABLE IF NOT EXISTS ops.pipeline_runs (
    run_id           uuid PRIMARY KEY,
    started_at       timestamptz NOT NULL,
    ended_at         timestamptz,
    status           text NOT NULL,
    rows_loaded      bigint,
    max_event_ts     timestamptz,
    dbt_state        jsonb,
    notes            text
);

-- Monitoring alerts (freshness/anomaly)
CREATE TABLE IF NOT EXISTS ops.monitoring_alerts (
    alert_id         uuid PRIMARY KEY,
    run_id           uuid REFERENCES ops.pipeline_runs(run_id),
    created_at       timestamptz NOT NULL,
    alert_type       text NOT NULL,
    severity         text NOT NULL,
    message          text NOT NULL,
    details          jsonb
);
