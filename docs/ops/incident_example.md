# Example incident: dashboard numbers wrong (missing events)

## Symptom
Stakeholder reports that “yesterday conversion is 0%” but traffic was normal.

## Triage
1) Check pipeline freshness (is data late?)
2) Check if one event type stopped (like purchase_completed)
3) Identify the first broken timestamp

## Queries
```sql
-- 1) Freshness
select max(event_ts) as max_event_ts, now() - max(event_ts) as lag
from raw.events;

-- 2) Event mix last 2 days
select
  date_trunc('hour', event_ts) as hour,
  event_name,
  count(*) as events
from raw.events
where event_ts >= now() - interval '2 days'
group by 1,2
order by 1 desc, 3 desc;

-- 3) First missing hour for purchase
with hours as (
  select generate_series(date_trunc('hour', now()-interval '48 hours'), date_trunc('hour', now()), interval '1 hour') as hour
), purchases as (
  select date_trunc('hour', event_ts) as hour, count(*) as n
  from raw.events
  where event_ts >= now() - interval '48 hours'
    and event_name='purchase_completed'
  group by 1
)
select h.hour, coalesce(p.n,0) as purchases
from hours h
left join purchases p using (hour)
order by h.hour;
```

## Resolution write-up (template)
- **Root cause:** …
- **Impact:** dashboards affected (which KPIs, time window)
- **Fix:** backfill / replay / corrected mapping
- **Prevention:** add monitor threshold + alert routing
