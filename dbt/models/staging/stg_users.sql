with events as (
    select * from {{ ref('stg_events') }}
),

first_seen as (
    select
        user_id,
        min(event_ts) as first_event_ts,
        min(case when event_name = 'app_open' then event_ts end) as first_app_open_ts,
        min(case when event_name = 'signup_completed' then event_ts end) as signup_completed_ts
    from events
    group by 1
),

user_variant as (
    select
        user_id,
        -- variant is assigned at user level in the generator, so take any non-null value
        max(variant) filter (where variant is not null) as variant,
        max(experiment_key) filter (where experiment_key is not null) as experiment_key
    from events
    group by 1
),

user_country as (
    select
        user_id,
        max(country) filter (where country is not null) as country
    from events
    group by 1
)

select
    f.user_id,
    f.first_event_ts,
    f.first_app_open_ts,
    f.signup_completed_ts,
    c.country,
    v.experiment_key,
    v.variant
from first_seen f
left join user_country c using (user_id)
left join user_variant v using (user_id)
