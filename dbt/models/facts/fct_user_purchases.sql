with orders as (
    select * from {{ ref('fct_orders') }}
)

select
    user_id,
    min(order_ts) as first_purchase_ts,
    count(*) as orders_count,
    sum(revenue) as total_revenue
from orders
group by 1
