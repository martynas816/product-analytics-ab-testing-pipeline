# Request: “What happened yesterday?” (daily KPI pulse)

## Goal
Give a fast, *numbers-first* update plus 1–2 likely drivers.

## Query (yesterday KPI snapshot)
```sql
-- Yesterday conversion + revenue (by variant)
with base as (
  select *
  from analytics.mart_conversion_daily
  where event_day >= current_date - interval '2 days'
)
select
  event_day::date as day,
  variant,
  users_exposed,
  users_started_checkout,
  users_purchased,
  checkout_to_purchase_rate_24h,
  revenue
from base
order by day desc, variant;
```

## Validation checks (before replying)
```sql
-- Data freshness
select max(event_ts) as max_event_ts
from raw.events;

-- Any missing variants?
select event_day::date as day, count(distinct variant) as variants
from analytics.mart_conversion_daily
where event_day >= current_date - interval '7 days'
group by 1
order by 1 desc;
```

## Response template (paste to Slack/email)
- **Yesterday (DATE):** conversion **X%** (control **X%**, treatment **X%**), revenue **€X**, users exposed **X**.
- **Change vs prev day:** conversion **+/- Xpp**, revenue **+/- €X**.
- **Top driver hypothesis (backed by numbers):** e.g. traffic mix shift / checkout-start drop / AOV shift.
- **Next action:** monitor next 24h; if persists, deep-dive by channel/device/country.
