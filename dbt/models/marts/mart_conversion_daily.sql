with checkouts as (
    select
        user_id,
        variant,
        date_trunc('day', event_ts) as event_day,
        min(event_ts) as first_checkout_ts
    from {{ ref('stg_events') }}
    where event_name = 'checkout_started'
    group by 1,2,3
),

purchases as (
    select
        user_id,
        min(event_ts) as first_purchase_ts
    from {{ ref('stg_events') }}
    where event_name = 'purchase_completed'
    group by 1
),

joined as (
    select
        c.event_day,
        coalesce(c.variant, 'unknown') as variant,
        c.user_id,
        c.first_checkout_ts,
        p.first_purchase_ts,
        case
            when p.first_purchase_ts is null then 0
            when p.first_purchase_ts >= c.first_checkout_ts
             and p.first_purchase_ts <  c.first_checkout_ts + interval '1 day' then 1
            else 0
        end as converted_24h
    from checkouts c
    left join purchases p using (user_id)
),

agg as (
    select
        event_day,
        variant,
        count(distinct user_id) as users_started_checkout,
        count(distinct case when converted_24h = 1 then user_id end) as users_purchased_24h
    from joined
    group by 1,2
)

select
    event_day,
    variant,
    users_started_checkout,
    users_purchased_24h,
    case when users_started_checkout = 0 then null else users_purchased_24h::numeric / users_started_checkout end as checkout_to_purchase_rate_24h
from agg
order by event_day, variant
