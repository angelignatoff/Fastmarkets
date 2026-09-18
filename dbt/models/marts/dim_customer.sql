select customer_id, customer_name, customer_phone, customer_email
from {{ ref('stg_customers') }}
