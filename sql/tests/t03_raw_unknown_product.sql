-- t03: raw sales must contain exactly 2 lines with an unknown product (planted).
SELECT 'unknown-product raw sale lines: expected 2, found ' || COUNT(*) AS violation
FROM raw_sales
WHERE product_code NOT IN (SELECT product_code FROM raw_products)
HAVING COUNT(*) <> 2;
