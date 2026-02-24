with purchases as (
    select
        order_id,
        user_id,
        event_ts as order_ts,
        revenue,
        items,
        currency,
        experiment_key,
        variant
    from {{ ref('stg_events') }}
    where event_name = 'purchase_completed'
      and order_id is not null
)

select
    order_id,
    user_id,
    order_ts,
    revenue,
    items,
    currency,
    experiment_key,
    variant
from purchases
