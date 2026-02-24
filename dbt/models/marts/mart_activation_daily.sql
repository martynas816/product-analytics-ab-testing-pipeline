with e as (
    select
        date_trunc('day', event_ts) as event_day,
        user_id,
        variant,
        experiment_key,
        event_name
    from {{ ref('stg_events') }}
    where event_name in ('app_open', 'signup_completed')
),

agg as (
    select
        event_day,
        coalesce(variant, 'unknown') as variant,
        count(distinct case when event_name='app_open' then user_id end) as users_opened,
        count(distinct case when event_name='signup_completed' then user_id end) as users_signed_up
    from e
    group by 1,2
)

select
    event_day,
    variant,
    users_opened,
    users_signed_up,
    case when users_opened = 0 then null else users_signed_up::numeric / users_opened end as activation_rate
from agg
order by event_day, variant
