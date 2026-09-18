with cleaned as (
    select
        customer_id,
        customer_name,
        trim(replace(customer_phone, '"', '')) as phone,
        lower(trim(customer_email)) as email,
        order_date,
        order_id
    from {{ ref('stg_orders') }}
)
select
    customer_id,
    customer_name,
    case when phone is null or upper(phone) in ('', 'N/A', 'NULL', '123456')
        then null else phone end as customer_phone,
    case when regexp_like(email, '^[a-z0-9._%+-]+@[a-z0-9.-]+[.][a-z]{2,}$')
        then email else null end as customer_email
from cleaned
qualify row_number() over (
    partition by customer_id order by order_date desc, order_id desc
) = 1
