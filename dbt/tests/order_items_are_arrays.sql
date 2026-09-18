select order_id
from {{ ref('stg_orders') }}
where not coalesce(is_array(order_items), false)
   or coalesce(array_size(order_items), 0) = 0
