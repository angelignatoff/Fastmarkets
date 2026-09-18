select
    try_to_number(customer_id, 38, 0) as customer_id,
    nullif(trim(customer_name), '') as customer_name,
    customer_phone,
    customer_email,
    try_to_number(order_id, 38, 0) as order_id,
    try_to_date(order_date, 'YYYY-MM-DD') as order_date,
    try_to_decimal(order_total, 18, 2) as order_total,
    try_parse_json(order_items) as order_items
from {{ source('raw', 'homework_obt') }}
