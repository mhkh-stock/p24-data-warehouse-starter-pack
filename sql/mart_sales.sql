-- P24 — mart_sales.sql (mart model)
-- Loads fact_sales from the enriched intermediate model.
-- Grain: one row per clean sale line (sale_line_id = raw_line_no).
-- fact_sales is the table the business queries: revenue, gross profit
-- and margin by product, category, customer, supplier or month.

INSERT INTO fact_sales
    (sale_line_id, order_id, sale_date, customer_id, product_code,
     qty, unit_price_pkr, line_total_pkr, cost_price_pkr,
     gross_profit_pkr, margin_pct)
SELECT
    sale_line_id, order_id, sale_date, customer_id, product_code,
    qty, unit_price_pkr, line_total_pkr, cost_price_pkr,
    gross_profit_pkr, margin_pct
FROM int_sales_enriched;

-- fact_purchases loads here too (same mart step, one load per fact).
INSERT INTO fact_purchases
    (po_line_id, po_id, purchase_date, supplier_id, product_code,
     qty, unit_cost_pkr, total_cost_pkr)
SELECT
    po_line_id, po_id, purchase_date, supplier_id, product_code,
    qty, unit_cost_pkr, total_cost_pkr
FROM stg_purchases;
