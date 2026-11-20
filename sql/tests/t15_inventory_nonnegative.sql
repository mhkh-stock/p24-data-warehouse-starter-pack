-- t15: inventory stock must never go negative (purchases cover sales per product).
SELECT * FROM mart_inventory WHERE stock_qty < 0;
