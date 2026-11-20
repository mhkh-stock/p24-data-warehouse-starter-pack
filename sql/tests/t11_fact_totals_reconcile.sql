-- t11: fact_sales totals must reconcile to staged totals (reconciliation).
SELECT 'fact gross ' || (SELECT SUM(line_total_pkr) FROM fact_sales)
       || ' <> staged gross ' || (SELECT SUM(line_total_pkr) FROM stg_sales)
       AS violation
WHERE (SELECT SUM(line_total_pkr) FROM fact_sales)
   <> (SELECT SUM(line_total_pkr) FROM stg_sales);
