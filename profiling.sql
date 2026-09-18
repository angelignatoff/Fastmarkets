USE ROLE HOMEWORK_ENGINEER;
USE WAREHOUSE HOMEWORK_WH;
USE DATABASE HOMEWORK;

SELECT COUNT(*) AS source_rows,
    COUNT(DISTINCT order_id) AS orders,
    COUNT(DISTINCT customer_id) AS customers,
    MIN(TRY_TO_DATE(order_date, 'YYYY-MM-DD')) AS first_order,
    MAX(TRY_TO_DATE(order_date, 'YYYY-MM-DD')) AS last_order
FROM RAW.HOMEWORK_OBT;

SELECT customer_phone, COUNT(*) AS records
FROM RAW.HOMEWORK_OBT
GROUP BY 1 ORDER BY 2 DESC LIMIT 20;

SELECT COUNT_IF(NOT COALESCE(REGEXP_LIKE(LOWER(TRIM(customer_email)),
    '^[a-z0-9._%+-]+@[a-z0-9.-]+[.][a-z]{2,}$'), FALSE)) AS invalid_emails
FROM RAW.HOMEWORK_OBT;

WITH item_totals AS (
    SELECT o.order_id,
        SUM(i.value:quantity::NUMBER(18,0) * i.value:price::NUMBER(18,2)) AS total
    FROM RAW.HOMEWORK_OBT o,
        LATERAL FLATTEN(INPUT => TRY_PARSE_JSON(o.order_items)) i
    GROUP BY 1
)
SELECT COUNT(*) AS mismatching_orders
FROM RAW.HOMEWORK_OBT o
LEFT JOIN item_totals i USING (order_id)
WHERE i.total IS NULL OR TRY_TO_DECIMAL(o.order_total,18,2) IS NULL
    OR ABS(TRY_TO_DECIMAL(o.order_total,18,2) - i.total) > 0.01;

SELECT i.value:product_id::VARCHAR AS product_id,
    i.value:product_name::VARCHAR AS product_name,
    COUNT(*) AS line_items,
    COUNT(DISTINCT i.value:price::NUMBER(18,2)) AS distinct_prices
FROM RAW.HOMEWORK_OBT o,
    LATERAL FLATTEN(INPUT => TRY_PARSE_JSON(o.order_items)) i
GROUP BY 1, 2;

WITH weekly AS (
    SELECT DATEADD(day, 1 - DAYOFWEEKISO(TO_DATE(o.order_date)), TO_DATE(o.order_date))::DATE AS week_start,
        i.value:product_id::VARCHAR AS product_id,
        SUM(i.value:quantity::NUMBER(18,0) * i.value:price::NUMBER(18,2)) AS revenue
    FROM RAW.HOMEWORK_OBT o,
        LATERAL FLATTEN(INPUT => TRY_PARSE_JSON(o.order_items)) i
    GROUP BY 1, 2
), ranked AS (
    SELECT *, DENSE_RANK() OVER (PARTITION BY week_start ORDER BY revenue DESC) AS ranking
    FROM weekly
)
SELECT product_id, COUNT(*) AS weeks_as_top_seller
FROM ranked WHERE ranking = 1
GROUP BY 1 ORDER BY 1;
