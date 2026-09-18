select product_id, product_name
from {{ ref('stg_order_items') }}
qualify row_number() over (
    partition by product_id order by order_date desc, order_id desc, line_number desc
) = 1
