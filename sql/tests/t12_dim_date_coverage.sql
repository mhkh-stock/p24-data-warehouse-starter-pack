-- t12: dim_date must cover 2026-01-01 .. 2026-06-30 with exactly 181 days, no gaps.
SELECT 'dim_date: expected 181 days 2026-01-01..2026-06-30, found '
       || COUNT(*) || ' rows, ' || MIN(date_key) || '..' || MAX(date_key)
       AS violation
FROM dim_date
HAVING COUNT(*) <> 181 OR MIN(date_key) <> '2026-01-01' OR MAX(date_key) <> '2026-06-30';
