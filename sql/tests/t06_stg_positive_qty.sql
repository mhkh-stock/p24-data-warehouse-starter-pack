-- t06: every staged sale line must have qty > 0.
SELECT * FROM stg_sales WHERE qty <= 0;
