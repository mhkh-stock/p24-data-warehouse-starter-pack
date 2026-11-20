-- t16: fact_purchases totals must reconcile to staged purchase totals.
SELECT 'fact purchase total ' || (SELECT SUM(total_cost_pkr) FROM fact_purchases)
       || ' <> staged total ' || (SELECT SUM(total_cost_pkr) FROM stg_purchases)
       AS violation
WHERE (SELECT SUM(total_cost_pkr) FROM fact_purchases)
   <> (SELECT SUM(total_cost_pkr) FROM stg_purchases);
