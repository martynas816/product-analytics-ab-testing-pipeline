with opens as (
    select
        user_id,
        variant,
        date_trunc('day', event_ts)::date as active_day
    from {{ ref('stg_events') }}
    where event_name = 'app_open'
),

cohorts as (
    select
        user_id,
        coalesce(variant, 'unknown') as variant,
        min(active_day) as cohort_day
    from opens
    group by 1,2
),

activity as (
    select
        c.cohort_day,
        c.variant,
        c.user_id,
        max(case when o.active_day = c.cohort_day + 1 then 1 else 0 end) as retained_d1,
        max(case when o.active_day = c.cohort_day + 7 then 1 else 0 end) as retained_d7
    from cohorts c
    left join opens o
        on o.user_id = c.user_id
    group by 1,2,3
),

agg as (
    select
        cohort_day,
        variant,
        count(*) as users_in_cohort,
        sum(retained_d1) as users_retained_d1,
        sum(retained_d7) as users_retained_d7
    from activity
    group by 1,2
)

select
    cohort_day,
    variant,
    users_in_cohort,
    users_retained_d1,
    users_retained_d7,
    case when users_in_cohort = 0 then null else users_retained_d1::numeric / users_in_cohort end as retention_d1,
    case when users_in_cohort = 0 then null else users_retained_d7::numeric / users_in_cohort end as retention_d7
from agg
order by cohort_day, variant
