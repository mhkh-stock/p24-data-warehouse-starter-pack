-- t04: raw sales must contain exactly 1 line with a wrong line total (planted).
SELECT 'wrong-total raw sale lines: expected 1, found ' || COUNT(*) AS violation
FROM raw_sales
WHERE line_total_pkr <> qty * unit_price_pkr
HAVING COUNT(*) <> 1;
