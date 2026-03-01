# Request: “Can you pull numbers for promotion X?”

## Assumption
Promotion is represented as a property on events (e.g. `promo_id`). If not, define an extraction rule (UTM / coupon code / campaign mapping).

## Query (promo performance)
```sql
-- Promo conversion + revenue by day
select
  date(event_ts) as day,
  properties->>'promo_id' as promo_id,
  count(distinct user_id) filter (where event_name = 'product_view') as viewers,
  count(distinct user_id) filter (where event_name = 'checkout_started') as checkout_starters,
  count(distinct user_id) filter (where event_name = 'purchase_completed') as purchasers,
  sum(case when event_name='purchase_completed' then (properties->>'revenue')::numeric else 0 end) as revenue
from raw.events
where event_ts >= now() - interval '30 days'
  and properties ? 'promo_id'
  and properties->>'promo_id' = 'PROMO_X'
group by 1,2
order by 1;
```

## Reply format
- Promo X (date range): **revenue €X**, **purchasers X**, **conversion X%**.
- vs baseline (non-promo): **+/- Xpp** conversion.
- Notes: attribution rules, data caveats.
