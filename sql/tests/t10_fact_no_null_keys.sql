-- t10: fact_sales must have no NULL keys (not-null check).
SELECT * FROM fact_sales
WHERE order_id IS NULL OR sale_date IS NULL OR customer_id IS NULL
   OR product_code IS NULL OR qty IS NULL OR line_total_pkr IS NULL;
