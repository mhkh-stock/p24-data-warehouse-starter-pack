-- t13: dim_product must hold exactly one row per product (SCD Type 1 — no history rows).
SELECT 'dim_product: expected 40 rows / 40 distinct codes, found '
       || COUNT(*) || ' rows / ' || COUNT(DISTINCT product_code) || ' codes'
       AS violation
FROM dim_product
HAVING COUNT(*) <> 40 OR COUNT(DISTINCT product_code) <> 40;
