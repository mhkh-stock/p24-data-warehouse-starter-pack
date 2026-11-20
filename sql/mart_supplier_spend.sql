-- P24 — mart_supplier_spend.sql (mart model)
-- Spend per supplier: total purchase cost, number of purchase orders,
-- distinct products supplied, and share of total spend.
-- Answers "who do we depend on?" — the supplier with the biggest share
-- is the one whose failure hurts most.

DROP TABLE IF EXISTS mart_supplier_spend;
CREATE TABLE mart_supplier_spend AS
SELECT
    f.supplier_id,
    d.supplier_name,
    COUNT(*) AS po_lines,
    COUNT(DISTINCT f.po_id) AS po_count,
    COUNT(DISTINCT f.product_code) AS products_supplied,
    SUM(f.total_cost_pkr) AS total_spend_pkr,
    ROUND(100.0 * SUM(f.total_cost_pkr)
          / (SELECT SUM(total_cost_pkr) FROM fact_purchases), 2) AS share_pct
FROM fact_purchases f
INNER JOIN dim_supplier d ON d.supplier_id = f.supplier_id
GROUP BY f.supplier_id, d.supplier_name;
