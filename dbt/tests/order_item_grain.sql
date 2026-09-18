select order_id, line_number
from {{ ref('fct_order_items') }}
group by 1, 2
having count(*) > 1
