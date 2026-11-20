-- P24 — stg_products.sql (staging model)
-- Cleans raw_products: the product master. Guards: cost and sell prices
-- must be positive, and sell price must be at or above cost price
-- (a product sold below cost is a data error until the owner confirms it).
-- Grain: one row per product_code.

DROP TABLE IF EXISTS stg_products;
CREATE TABLE stg_products AS
SELECT
    product_code,
    product_name,
    category,
    supplier_id,
    unit,
    CAST(cost_price_pkr AS INTEGER) AS cost_price_pkr,
    CAST(sell_price_pkr AS INTEGER) AS sell_price_pkr
FROM raw_products
WHERE cost_price_pkr > 0
  AND sell_price_pkr >= cost_price_pkr;
