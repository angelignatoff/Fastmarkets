select week_start, product_id
from {{ ref('agg_weekly_product') }}
group by 1, 2
having count(*) > 1
