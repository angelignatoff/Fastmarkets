with expected as (
    select count(*) as orders, coalesce(sum(array_size(order_items)), 0) as items
    from {{ ref('stg_orders') }}
)
select 'orders' as entity
from expected
where orders <> (select count(*) from {{ ref('fct_orders') }})
union all
select 'items'
from expected
where items <> (select count(*) from {{ ref('fct_order_items') }})
union all
select 'source_empty'
where not exists (select 1 from {{ source('raw', 'homework_obt') }})
