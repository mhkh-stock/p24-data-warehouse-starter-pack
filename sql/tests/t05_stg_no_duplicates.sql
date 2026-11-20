-- t05: stg_sales must have no duplicate lines left.
SELECT order_id, sale_date, customer_id, product_code, qty,
       unit_price_pkr, line_total_pkr, COUNT(*) AS n
FROM stg_sales
GROUP BY 1, 2, 3, 4, 5, 6, 7
HAVING COUNT(*) > 1;
