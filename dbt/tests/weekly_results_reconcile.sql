with expected as (
    select
        {{ week_start('order_date') }} as week_start,
        product_id,
        sum(quantity) as units_sold,
        count(distinct order_id) as order_count,
        sum(line_revenue) as revenue
    from {{ ref('fct_order_items') }}
    group by 1, 2
), ranked as (
    select *, dense_rank() over (partition by week_start order by revenue desc) as ranking
    from expected
)
select coalesce(e.week_start, a.week_start) as week_start,
    coalesce(e.product_id, a.product_id) as product_id
from ranked e
full outer join {{ ref('agg_weekly_product') }} a
    on e.week_start = a.week_start and e.product_id = a.product_id
where e.product_id is null or a.product_id is null
   or a.units_sold is distinct from e.units_sold
   or a.order_count is distinct from e.order_count
   or a.revenue is distinct from e.revenue
   or a.is_top_seller is distinct from iff(e.ranking = 1, 1, 0)
