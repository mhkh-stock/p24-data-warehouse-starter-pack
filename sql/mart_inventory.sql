-- P24 — mart_inventory.sql (mart model)
-- Stock on hand per product: everything bought minus everything sold.
--   stock_qty   = purchased_qty - sold_qty
--   stock_value = stock_qty * cost_price_pkr  (standard cost from dim_product)
-- Status rule (stated, not hidden): stock below 10% of what was bought
-- in the period is LOW — reorder. Stock of zero or less is OUT.
-- The SAMPLE data was built so purchases cover sales for every product,
-- so a negative stock here means the load is wrong, and test t15 fails.

DROP TABLE IF EXISTS mart_inventory;
CREATE TABLE mart_inventory AS
SELECT
    p.product_code,
    p.product_name,
    p.category,
    p.supplier_id,
    COALESCE(pur.purchased_qty, 0) AS purchased_qty,
    COALESCE(s.sold_qty, 0) AS sold_qty,
    COALESCE(pur.purchased_qty, 0) - COALESCE(s.sold_qty, 0) AS stock_qty,
    (COALESCE(pur.purchased_qty, 0) - COALESCE(s.sold_qty, 0))
        * p.cost_price_pkr AS stock_value_pkr,
    CASE
        WHEN COALESCE(pur.purchased_qty, 0) - COALESCE(s.sold_qty, 0) <= 0 THEN 'OUT'
        WHEN COALESCE(pur.purchased_qty, 0) - COALESCE(s.sold_qty, 0)
             < 0.10 * COALESCE(pur.purchased_qty, 0) THEN 'LOW'
        ELSE 'OK'
    END AS stock_status
FROM dim_product p
LEFT JOIN (
    SELECT product_code, SUM(qty) AS purchased_qty
    FROM fact_purchases GROUP BY product_code
) pur ON pur.product_code = p.product_code
LEFT JOIN (
    SELECT product_code, SUM(qty) AS sold_qty
    FROM fact_sales GROUP BY product_code
) s ON s.product_code = p.product_code;
