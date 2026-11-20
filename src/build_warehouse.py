"""Build the Khan Traders (SAMPLE) warehouse into data/processed/warehouse.db.

Order of operations:
  1. schema.sql            — raw landing tables + star-schema DDL
  2. load raw CSVs into raw_sales / raw_purchases / raw_products
  3. stg_*.sql             — staging models (cleaning, rejection guards)
  4. int_sales_enriched.sql — intermediate model (joins + margins)
  5. load_dimensions.sql   — dim_product / dim_supplier / dim_customer / dim_date
  6. mart_sales.sql        — fact_sales + fact_purchases
  7. mart_inventory.sql + mart_supplier_spend.sql — marts
  8. export processed CSVs the workbook and report read from

Rejection counts per reason are printed, so the build log shows exactly
which raw lines were dropped and why (the 8 planted defects).

Usage:  python3 src/build_warehouse.py
"""
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SQL = ROOT / "sql"
DB = ROOT / "data" / "processed" / "warehouse.db"
PROCESSED = ROOT / "data" / "processed"

MODELS = [
    "stg_sales.sql",
    "stg_purchases.sql",
    "stg_products.sql",
    "int_sales_enriched.sql",
    "load_dimensions.sql",
    "mart_sales.sql",
    "mart_inventory.sql",
    "mart_supplier_spend.sql",
]


def run_sql(conn, path):
    conn.executescript(path.read_text(encoding="utf-8"))


def load_csv(conn, table, path, columns):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    placeholders = ", ".join("?" * (len(columns) + 1))
    cols = "raw_line_no, " + ", ".join(columns)
    for i, row in enumerate(rows, start=1):
        conn.execute(
            f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
            [i] + [row[c] for c in columns],
        )
    return len(rows)


def one(conn, sql):
    return conn.execute(sql).fetchone()[0]


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    if DB.exists():
        DB.unlink()
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")

    run_sql(conn, SQL / "schema.sql")

    n_sales = load_csv(conn, "raw_sales", ROOT / "data/raw/sales_SAMPLE.csv",
                       ["order_id", "sale_date", "customer_id", "product_code",
                        "qty", "unit_price_pkr", "line_total_pkr"])
    n_purch = load_csv(conn, "raw_purchases", ROOT / "data/raw/purchases_SAMPLE.csv",
                       ["po_id", "purchase_date", "supplier_id", "product_code",
                        "qty", "unit_cost_pkr", "total_cost_pkr"])
    n_prod = load_csv(conn, "raw_products", ROOT / "data/raw/products_SAMPLE.csv",
                      ["product_code", "product_name", "category", "supplier_id",
                       "unit", "cost_price_pkr", "sell_price_pkr"])
    conn.commit()
    print(f"raw_sales:     {n_sales} lines")
    print(f"raw_purchases: {n_purch} lines")
    print(f"raw_products:  {n_prod} products")

    for model in MODELS:
        run_sql(conn, SQL / model)
        conn.commit()
        print(f"ran {model}")

    # --- rejection breakdown (why each raw sale line was dropped) ---
    dup = one(conn, """SELECT COUNT(*) FROM (
        SELECT 1 FROM raw_sales GROUP BY order_id, sale_date, customer_id,
        product_code, qty, unit_price_pkr, line_total_pkr HAVING COUNT(*) > 1)""")
    # duplicate *extra* lines = total rows - distinct rows
    dup_extra = n_sales - one(conn, """SELECT COUNT(*) FROM (
        SELECT DISTINCT order_id, sale_date, customer_id, product_code,
        qty, unit_price_pkr, line_total_pkr FROM raw_sales)""")
    bad_qty = one(conn, "SELECT COUNT(*) FROM raw_sales WHERE qty <= 0")
    unknown = one(conn, """SELECT COUNT(*) FROM raw_sales WHERE product_code
        NOT IN (SELECT product_code FROM raw_products)""")
    bad_total = one(conn, """SELECT COUNT(*) FROM raw_sales
        WHERE line_total_pkr <> qty * unit_price_pkr""")
    print(f"rejected: {dup_extra} duplicate lines, {bad_qty} qty<=0 lines, "
          f"{unknown} unknown-product lines, {bad_total} wrong-total lines")
    print(f"rejected total: {n_sales - one(conn, 'SELECT COUNT(*) FROM stg_sales')} "
          f"of {n_sales} raw sale lines")

    # --- row counts per table ---
    print("\nrow counts:")
    for table in ["stg_sales", "stg_purchases", "stg_products",
                  "int_sales_enriched", "dim_date", "dim_product",
                  "dim_customer", "dim_supplier", "fact_sales",
                  "fact_purchases", "mart_inventory", "mart_supplier_spend"]:
        print(f"  {table:<22} {one(conn, f'SELECT COUNT(*) FROM {table}')}")

    # --- headline totals ---
    gross = one(conn, "SELECT SUM(line_total_pkr) FROM fact_sales")
    profit = one(conn, "SELECT SUM(gross_profit_pkr) FROM fact_sales")
    spend = one(conn, "SELECT SUM(total_cost_pkr) FROM fact_purchases")
    stock = one(conn, "SELECT SUM(stock_value_pkr) FROM mart_inventory")
    print(f"\nsales gross (clean):   PKR {gross:,}")
    print(f"gross profit (clean):  PKR {profit:,}")
    print(f"purchase spend:        PKR {spend:,}")
    print(f"inventory value:       PKR {stock:,}")

    # --- processed CSV exports ---
    exports = {
        "fact_sales.csv": "SELECT * FROM fact_sales ORDER BY sale_line_id",
        "fact_purchases.csv": "SELECT * FROM fact_purchases ORDER BY po_line_id",
        "mart_inventory.csv": "SELECT * FROM mart_inventory ORDER BY product_code",
        "mart_supplier_spend.csv": "SELECT * FROM mart_supplier_spend ORDER BY total_spend_pkr DESC",
        "sales_by_category.csv": """SELECT category, COUNT(*) AS lines,
            SUM(qty) AS units_sold, SUM(line_total_pkr) AS gross_pkr,
            SUM(gross_profit_pkr) AS gross_profit_pkr
            FROM int_sales_enriched GROUP BY category ORDER BY gross_pkr DESC""",
        "sales_by_month.csv": """SELECT substr(sale_date, 1, 7) AS month,
            COUNT(*) AS lines, SUM(qty) AS units_sold,
            SUM(line_total_pkr) AS gross_pkr, SUM(gross_profit_pkr) AS gross_profit_pkr
            FROM fact_sales GROUP BY month ORDER BY month""",
    }
    for name, query in exports.items():
        cur = conn.execute(query)
        with open(PROCESSED / name, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([d[0] for d in cur.description])
            w.writerows(cur.fetchall())
        print(f"wrote data/processed/{name}")

    conn.close()
    print(f"\nwarehouse built: data/processed/warehouse.db")


if __name__ == "__main__":
    main()
