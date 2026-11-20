-- t09: fact_sales grain — one fact row per staged sale line.
SELECT 'fact_sales rows: expected ' || (SELECT COUNT(*) FROM stg_sales)
       || ', found ' || (SELECT COUNT(*) FROM fact_sales) AS violation
WHERE (SELECT COUNT(*) FROM fact_sales) <> (SELECT COUNT(*) FROM stg_sales);
