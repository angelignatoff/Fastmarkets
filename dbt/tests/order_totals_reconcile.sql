with items as (
    select order_id, sum(line_revenue) as item_total, count(*) as item_count
    from {{ ref('fct_order_items') }}
    group by order_id
)
select o.order_id, o.order_total, i.item_total
from {{ ref('fct_orders') }} o
left join items i using (order_id)
where i.item_count is null
   or i.item_total is null
   or o.order_total is null
   or abs(o.order_total - i.item_total) > 0.01
