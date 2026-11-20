-- P24 — load_dimensions.sql
-- Loads the four dimensions. The customer and supplier masters are small
-- reference lists the client keeps outside the transaction exports, so
-- they are loaded here as VALUES (documented in data/README.md); the
-- product master comes from the products CSV via stg_products, and the
-- date dimension is generated for the whole period with a recursive CTE.
-- SCD policy: dim_product is Type 1 — one row per product, overwritten
-- when a price changes. History is NOT kept; if the client later needs
-- price history, dim_product becomes Type 2 (valid_from / valid_to).
-- dim_date covers 2026-01-01 .. 2026-06-30 (181 days), the full SAMPLE
-- period, so every sale and purchase date joins.

-- dim_product (SCD Type 1)
INSERT INTO dim_product
SELECT product_code, product_name, category, supplier_id, unit,
       cost_price_pkr, sell_price_pkr
FROM stg_products;

-- dim_supplier (reference list)
INSERT INTO dim_supplier (supplier_id, supplier_name, city) VALUES
('SUP-01', 'Punjab Rice Mills', 'Gujranwala'),
('SUP-02', 'Al-Noor Flour Mills', 'Lahore'),
('SUP-03', 'Ravi Sugar Traders', 'Faisalabad'),
('SUP-04', 'Noor Oil Mills', 'Lahore'),
('SUP-05', 'Lahore Pulses Traders', 'Akbari Mandi, Lahore'),
('SUP-06', 'Shahi Masala Traders', 'Lahore'),
('SUP-07', 'Chaman Tea Traders', 'Lahore'),
('SUP-08', 'City Household Distributors', 'Lahore');

-- dim_customer (reference list — the 25 shops Khan Traders supplies)
INSERT INTO dim_customer (customer_id, customer_name, area, city) VALUES
('CUS-01', 'Bilal General Store', 'Shah Alam Market', 'Lahore'),
('CUS-02', 'Al-Madina Karyana Store', 'Akbari Mandi', 'Lahore'),
('CUS-03', 'Usman Traders', 'Urdu Bazaar', 'Lahore'),
('CUS-04', 'Haji Sons General Store', 'Ichhra', 'Lahore'),
('CUS-05', 'Rehman Karyana', 'Township', 'Lahore'),
('CUS-06', 'Al-Falah Store', 'Gulberg III', 'Lahore'),
('CUS-07', 'Chaudhry General Store', 'Model Town', 'Lahore'),
('CUS-08', 'Zain Traders', 'Johar Town', 'Lahore'),
('CUS-09', 'Bismillah Karyana', 'Samanabad', 'Lahore'),
('CUS-10', 'Noor General Store', 'DHA Phase 4', 'Lahore'),
('CUS-11', 'Ahmad Cash & Carry', 'Wahdat Road', 'Lahore'),
('CUS-12', 'Ghulam Rasool & Sons', 'Badami Bagh', 'Lahore'),
('CUS-13', 'Shahzad Super Store', 'Faisal Town', 'Lahore'),
('CUS-14', 'Al-Habib Karyana', 'Green Town', 'Lahore'),
('CUS-15', 'Malik General Store', 'Sabzazar', 'Lahore'),
('CUS-16', 'Rana Traders', 'Cavalry Ground', 'Lahore'),
('CUS-17', 'Imran Store', 'Mughalpura', 'Lahore'),
('CUS-18', 'Siddique General Store', 'Shadbagh', 'Lahore'),
('CUS-19', 'Al-Rehman Cash & Carry', 'Allama Iqbal Town', 'Lahore'),
('CUS-20', 'Khan General Store', 'Ravi Road', 'Lahore'),
('CUS-21', 'Farooq Karyana Store', 'Bhatti Gate', 'Lahore'),
('CUS-22', 'Naseer Traders', 'Misri Shah', 'Lahore'),
('CUS-23', 'Tariq Super Store', 'Wapda Town', 'Lahore'),
('CUS-24', 'Al-Noor General Store', 'Cantt', 'Lahore'),
('CUS-25', 'Hassan Cash & Carry', 'Gulshan-e-Ravi', 'Lahore');

-- dim_date: every day 2026-01-01 .. 2026-06-30
WITH RECURSIVE days(d) AS (
    SELECT DATE('2026-01-01')
    UNION ALL
    SELECT DATE(d, '+1 day') FROM days WHERE d < DATE('2026-06-30')
)
INSERT INTO dim_date
SELECT
    d AS date_key,
    d AS full_date,
    CAST(strftime('%Y', d) AS INTEGER) AS year,
    CAST(strftime('%m', d) AS INTEGER) AS month,
    CASE CAST(strftime('%m', d) AS INTEGER)
        WHEN 1 THEN 'January' WHEN 2 THEN 'February' WHEN 3 THEN 'March'
        WHEN 4 THEN 'April' WHEN 5 THEN 'May' WHEN 6 THEN 'June'
        WHEN 7 THEN 'July' WHEN 8 THEN 'August' WHEN 9 THEN 'September'
        WHEN 10 THEN 'October' WHEN 11 THEN 'November' ELSE 'December' END AS month_name,
    (CAST(strftime('%m', d) AS INTEGER) - 1) / 3 + 1 AS quarter,
    CAST(strftime('%w', d) AS INTEGER) AS day_of_week,
    CASE CAST(strftime('%w', d) AS INTEGER)
        WHEN 0 THEN 'Sunday' WHEN 1 THEN 'Monday' WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday' WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday'
        ELSE 'Saturday' END AS day_name,
    CASE WHEN CAST(strftime('%w', d) AS INTEGER) IN (0, 6) THEN 1 ELSE 0 END AS is_weekend
FROM days;
