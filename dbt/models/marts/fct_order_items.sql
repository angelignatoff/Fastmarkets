select order_item_id, order_id, line_number, customer_id, order_date,
    product_id, quantity, unit_price, line_revenue
from {{ ref('stg_order_items') }}
