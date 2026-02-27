# Request: “Why did this KPI change?” (KPI movement drill-down)

## Approach
1) Confirm it’s real (data quality). 2) Quantify *where* the change came from (segment decomposition). 3) Provide a short explanation + next step.

## Step 1 — confirm data is trustworthy
```sql
-- Compare counts in raw vs mart for last 2 days
select
  date(event_ts) as day,
  count(*) as raw_events
from raw.events
where event_ts >= now() - interval '2 days'
group by 1
order by 1 desc;

select
  event_day::date as day,
  sum(users_exposed) as exposed
from analytics.mart_conversion_daily
where event_day >= current_date - interval '2 days'
group by 1
order by 1 desc;
```

## Step 2 — localize the drop
Example: conversion dropped. Check which stage moved.
```sql
select
  event_day::date as day,
  variant,
  users_exposed,
  users_started_checkout,
  users_purchased,
  (users_started_checkout::float / nullif(users_exposed,0)) as exposure_to_checkout,
  (users_purchased::float / nullif(users_started_checkout,0)) as checkout_to_purchase
from analytics.mart_conversion_daily
where event_day >= current_date - interval '7 days'
order by day desc, variant;
```

## Response template
- KPI change is **real / likely data issue** because …
- The movement is driven mostly by **(stage)**: exposure→checkout changed **Xpp** while checkout→purchase changed **Ypp**.
- Most likely explanation: **(1 sentence)**.
- Next: segment by **channel/device/country** and report back with top 2 deltas.
