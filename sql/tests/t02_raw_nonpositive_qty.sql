-- t02: raw sales must contain exactly 3 lines with qty <= 0 (planted).
SELECT 'qty<=0 raw sale lines: expected 3, found ' || COUNT(*) AS violation
FROM raw_sales
WHERE qty <= 0
HAVING COUNT(*) <> 3;
