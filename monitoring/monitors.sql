-- Freshness monitor: data should be "recent enough"
-- Threshold is evaluated in code (default 24 hours)
select
  max(event_ts) as max_event_ts,
  now() - max(event_ts) as lag
from raw.events;

-- Anomaly monitor: conversion rate z-score (per variant) for most recent day
with daily as (
  select
    event_day::date as day,
    variant,
    users_started_checkout,
    checkout_to_purchase_rate_24h as rate
  from analytics.mart_conversion_daily
  where event_day >= now() - interval '45 days'
    and variant in ('control','treatment')
),

latest_day as (
  select max(day) as day from daily
),

baseline as (
  select
    d.variant,
    avg(d.rate) as mean_rate,
    stddev_pop(d.rate) as std_rate
  from daily d
  join latest_day l on d.day < l.day
  where d.users_started_checkout >= 200
  group by 1
),

latest as (
  select
    d.variant,
    d.day,
    d.users_started_checkout,
    d.rate
  from daily d
  join latest_day l on d.day = l.day
)

select
  l.variant,
  l.day,
  l.users_started_checkout,
  l.rate,
  b.mean_rate,
  b.std_rate,
  case when b.std_rate is null or b.std_rate = 0 then null else (l.rate - b.mean_rate) / b.std_rate end as z_score
from latest l
left join baseline b on b.variant = l.variant
order by l.variant;
