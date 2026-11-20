-- P24 — stg_purchases.sql (staging model)
-- Cleans raw_purchases. The SAMPLE purchase file has no planted defects,
-- so this model is a pass-through with the same guards as stg_sales:
-- qty must be positive, the product must exist in the master, and the
-- total must equal qty * unit cost. Any line failing a guard is rejected
-- and counted in the build log instead of silently loaded.

DROP TABLE IF EXISTS stg_purchases;
CREATE TABLE stg_purchases AS
SELECT
    raw_line_no AS po_line_id,
    po_id,
    purchase_date,
    supplier_id,
    product_code,
    CAST(qty AS INTEGER) AS qty,
    CAST(unit_cost_pkr AS INTEGER) AS unit_cost_pkr,
    CAST(total_cost_pkr AS INTEGER) AS total_cost_pkr
FROM raw_purchases
WHERE qty > 0
  AND product_code IN (SELECT product_code FROM raw_products)
  AND total_cost_pkr = qty * unit_cost_pkr;
