select
    o.order_id,
    i.index::integer as line_number,
    o.order_id::varchar || ':' || i.index::varchar as order_item_id,
    o.customer_id,
    o.order_date,
    nullif(trim(i.value:product_id::varchar), '') as product_id,
    nullif(trim(i.value:product_name::varchar), '') as product_name,
    try_to_decimal(i.value:quantity::varchar, 18, 0) as quantity,
    try_to_decimal(i.value:price::varchar, 18, 2) as unit_price,
    (try_to_decimal(i.value:quantity::varchar, 18, 0)
        * try_to_decimal(i.value:price::varchar, 18, 2))::number(20, 2) as line_revenue
from {{ ref('stg_orders') }} o,
    lateral flatten(input => o.order_items) i
