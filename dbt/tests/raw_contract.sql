select *
from {{ source('raw', 'homework_obt') }}
where not coalesce(regexp_like(customer_id, '^[0-9]+$'), false)
   or not coalesce(regexp_like(order_id, '^[0-9]+$'), false)
   or nullif(trim(customer_name), '') is null
   or try_to_date(order_date, 'YYYY-MM-DD') is null
   or not coalesce(regexp_like(order_total, '^[0-9]+([.][0-9]{1,2})?$'), false)
   or try_to_decimal(order_total, 18, 2) is null
