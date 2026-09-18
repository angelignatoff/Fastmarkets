{{ config(materialized='view') }}

with weekly as (
    select
        {{ week_start('order_date') }} as week_start,
        product_id,
        sum(quantity) as units_sold,
        count(distinct order_id) as order_count,
        sum(line_revenue) as revenue
    from {{ ref('fct_order_items') }}
    group by 1, 2
)
select
    w.week_start,
    w.product_id,
    p.product_name,
    w.units_sold,
    w.order_count,
    w.revenue,
    {{ top_seller_flag('w.revenue', 'w.week_start') }} as is_top_seller
from weekly w
join {{ ref('dim_product') }} p using (product_id)
