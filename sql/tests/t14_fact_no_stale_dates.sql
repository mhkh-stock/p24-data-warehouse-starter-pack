-- t14: no fact sale date may fall outside Jan–Jun 2026 (stale / out-of-range dates).
SELECT * FROM fact_sales
WHERE sale_date < '2026-01-01' OR sale_date > '2026-06-30';
