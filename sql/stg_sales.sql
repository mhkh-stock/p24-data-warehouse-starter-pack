-- P24 — stg_sales.sql (staging model)
-- Cleans raw_sales into one row per genuine sale line.
-- Rejects, with the reason recorded in the build log (see src/build_warehouse.py):
--   1. exact duplicate lines (same order, date, customer, product, qty, prices)
--   2. qty <= 0 (a sale cannot sell zero or a negative amount)
--   3. product_code not in the product master (unknown product)
--   4. line_total_pkr <> qty * unit_price_pkr (wrong line total)
-- Casting: dates kept as TEXT yyyy-mm-dd (SQLite has no DATE type);
-- qty / prices cast to INTEGER so a stray decimal fails loudly, not silently.
-- Grain after this model: one row per sale line. sale_line_id = raw_line_no.

DROP TABLE IF EXISTS stg_sales;
CREATE TABLE stg_sales AS
SELECT
    raw_line_no AS sale_line_id,
    order_id,
    sale_date,
    customer_id,
    product_code,
    CAST(qty AS INTEGER) AS qty,
    CAST(unit_price_pkr AS INTEGER) AS unit_price_pkr,
    CAST(line_total_pkr AS INTEGER) AS line_total_pkr
FROM raw_sales
WHERE qty > 0
  AND product_code IN (SELECT product_code FROM raw_products)
  AND line_total_pkr = qty * unit_price_pkr
  -- exact duplicates: keep the first occurrence only (lowest raw_line_no)
  AND raw_line_no IN (
      SELECT MIN(raw_line_no)
      FROM raw_sales
      GROUP BY order_id, sale_date, customer_id, product_code,
               qty, unit_price_pkr, line_total_pkr
  );
