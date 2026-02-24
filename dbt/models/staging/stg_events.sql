with base as (
    select
        event_id::uuid                  as event_id,
        event_ts                        as event_ts,
        user_id                         as user_id,
        session_id                      as session_id,
        event_name                       as event_name,
        properties                       as properties,
        experiment_key                   as experiment_key,
        variant                          as variant
    from raw.events
),

parsed as (
    select
        event_id,
        event_ts,
        user_id,
        session_id,
        event_name,
        experiment_key,
        nullif(variant, '') as variant,

        -- common properties
        nullif(properties->>'platform','') as platform,
        nullif(properties->>'referrer','') as referrer,

        -- signup properties
        nullif(properties->>'signup_method','') as signup_method,
        nullif(properties->>'country','') as country,

        -- product properties
        nullif(properties->>'product_id','') as product_id,
        nullif(properties->>'category','') as category,
        nullif(properties->>'price','')::numeric as price,
        nullif(properties->>'quantity','')::int as quantity,

        -- checkout properties
        nullif(properties->>'cart_value','')::numeric as cart_value,
        nullif(properties->>'items','')::int as items,

        -- purchase properties
        nullif(properties->>'order_id','') as order_id,
        nullif(properties->>'revenue','')::numeric as revenue,
        nullif(properties->>'currency','') as currency

    from base
)

select * from parsed
