-- t07: every staged sale line must reference a known product (referential integrity).
SELECT * FROM stg_sales
WHERE product_code NOT IN (SELECT product_code FROM dim_product);
