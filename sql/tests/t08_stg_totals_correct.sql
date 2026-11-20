-- t08: every staged sale line total must equal qty * unit price.
SELECT * FROM stg_sales WHERE line_total_pkr <> qty * unit_price_pkr;
