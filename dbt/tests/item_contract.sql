select o.order_id, i.index as line_number
from {{ ref('stg_orders') }} o, lateral flatten(input => o.order_items) i
where not coalesce(is_object(i.value), false)
   or not coalesce(is_varchar(i.value:product_id), false)
   or nullif(trim(i.value:product_id::varchar), '') is null
   or not coalesce(is_varchar(i.value:product_name), false)
   or nullif(trim(i.value:product_name::varchar), '') is null
   or not coalesce(regexp_like(i.value:quantity::varchar, '^[0-9]+([.]0+)?$'), false)
   or coalesce(try_to_decimal(i.value:quantity::varchar, 18, 0), 0) <= 0
   or not coalesce(regexp_like(i.value:price::varchar, '^[0-9]+([.][0-9]{1,2})?$'), false)
   or try_to_decimal(i.value:price::varchar, 18, 2) is null
