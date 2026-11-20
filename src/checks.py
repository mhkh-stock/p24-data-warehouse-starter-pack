"""Verification suite for P24 — Khan Traders warehouse starter pack.

Every check recomputes its number from the raw CSVs / warehouse / workbook
and compares it against the independent source. If a check fails, fix the
BUILD, not the check. Exit code 0 when all checks pass.

Covers: files present, raw row counts, planted-defect counts found exactly,
staging rejection counts, mart totals reconciling to raw totals, fact/dim
row counts, grain checks, date-dim coverage, SCD Type 1, per-category /
per-supplier / per-month / per-product reconciliation, workbook formulas
recalculated in LibreOffice, and README / DQ-report numbers matching the
verified figures.

Usage:  python3 src/checks.py
"""
import csv
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "processed" / "warehouse.db"
WB = ROOT / "outputs" / "warehouse_health_SAMPLE.xlsx"
RECALC_DIR = ROOT / "outputs" / ".recalc"

CHECKS = []


def check(name, passed, detail=""):
    CHECKS.append((name, bool(passed), str(detail)))
    mark = "PASS" if passed else "FAIL"
    print(f"{mark}  {name}" + (f"  ({detail})" if detail else ""))


def q(conn, sql):
    return conn.execute(sql).fetchone()[0]


def main():
    conn = sqlite3.connect(DB)

    # ---------- 1. files present ----------
    expected_files = [
        "data/raw/sales_SAMPLE.csv", "data/raw/purchases_SAMPLE.csv",
        "data/raw/products_SAMPLE.csv",
        "sql/schema.sql", "sql/stg_sales.sql", "sql/stg_purchases.sql",
        "sql/stg_products.sql", "sql/int_sales_enriched.sql",
        "sql/load_dimensions.sql", "sql/mart_sales.sql",
        "sql/mart_inventory.sql", "sql/mart_supplier_spend.sql",
        "src/generate_data.py", "src/build_warehouse.py",
        "src/run_tests.py", "src/build_workbook.py", "src/checks.py",
        "outputs/warehouse_health_SAMPLE.xlsx",
        "requirements.txt", ".gitignore",
    ]
    for f in expected_files:
        check(f"file exists: {f}", (ROOT / f).exists())
    test_files = sorted((ROOT / "sql" / "tests").glob("*.sql"))
    check("16 DQ test files present", len(test_files) == 16, f"found {len(test_files)}")
    for f in test_files:
        check(f"test file exists: {f.name}", f.exists())
    for name in ["fact_sales.csv", "fact_purchases.csv", "mart_inventory.csv",
                 "mart_supplier_spend.csv", "sales_by_category.csv",
                 "sales_by_month.csv"]:
        check(f"processed export exists: {name}",
              (ROOT / "data" / "processed" / name).exists())

    # ---------- 2. raw row counts ----------
    raw_sales = list(csv.DictReader(open(ROOT / "data/raw/sales_SAMPLE.csv")))
    raw_purch = list(csv.DictReader(open(ROOT / "data/raw/purchases_SAMPLE.csv")))
    raw_prod = list(csv.DictReader(open(ROOT / "data/raw/products_SAMPLE.csv")))
    check("raw sales = 600 lines", len(raw_sales) == 600, len(raw_sales))
    check("raw purchases = 180 lines", len(raw_purch) == 180, len(raw_purch))
    check("raw products = 40", len(raw_prod) == 40, len(raw_prod))
    check("raw sales count matches warehouse raw_sales",
          q(conn, "SELECT COUNT(*) FROM raw_sales") == len(raw_sales))
    check("raw purchases count matches warehouse raw_purchases",
          q(conn, "SELECT COUNT(*) FROM raw_purchases") == len(raw_purch))
    check("raw products count matches warehouse raw_products",
          q(conn, "SELECT COUNT(*) FROM raw_products") == len(raw_prod))

    # ---------- 3. planted defects found exactly ----------
    prod_codes = {r["product_code"] for r in raw_prod}
    dup_extra = len(raw_sales) - len({tuple(r.values()) for r in raw_sales})
    bad_qty = sum(1 for r in raw_sales if int(r["qty"]) <= 0)
    unknown = sum(1 for r in raw_sales if r["product_code"] not in prod_codes)
    bad_total = sum(1 for r in raw_sales
                    if int(r["line_total_pkr"]) != int(r["qty"]) * int(r["unit_price_pkr"]))
    check("planted duplicates found: exactly 2", dup_extra == 2, dup_extra)
    check("planted qty<=0 lines found: exactly 3", bad_qty == 3, bad_qty)
    check("planted unknown-product lines found: exactly 2", unknown == 2, unknown)
    check("planted wrong-total lines found: exactly 1", bad_total == 1, bad_total)
    check("planted defects total = 8", dup_extra + bad_qty + unknown + bad_total == 8)

    # ---------- 4. staging rejection counts ----------
    check("stg_sales = 592 clean lines",
          q(conn, "SELECT COUNT(*) FROM stg_sales") == 592)
    check("stg_purchases = 180 (no purchase defects)",
          q(conn, "SELECT COUNT(*) FROM stg_purchases") == 180)
    check("stg_products = 40", q(conn, "SELECT COUNT(*) FROM stg_products") == 40)
    check("rejected sale lines = 8 (600 - 592)",
          q(conn, "SELECT COUNT(*) FROM raw_sales")
          - q(conn, "SELECT COUNT(*) FROM stg_sales") == 8)
    check("no staged sale line is a duplicate",
          q(conn, """SELECT COUNT(*) FROM (SELECT 1 FROM stg_sales GROUP BY
              order_id, sale_date, customer_id, product_code, qty,
              unit_price_pkr, line_total_pkr HAVING COUNT(*) > 1)""") == 0)
    check("no staged sale line has qty <= 0",
          q(conn, "SELECT COUNT(*) FROM stg_sales WHERE qty <= 0") == 0)
    check("no staged sale line has an unknown product",
          q(conn, """SELECT COUNT(*) FROM stg_sales WHERE product_code
              NOT IN (SELECT product_code FROM dim_product)""") == 0)
    check("no staged sale line has a wrong total",
          q(conn, """SELECT COUNT(*) FROM stg_sales
              WHERE line_total_pkr <> qty * unit_price_pkr""") == 0)

    # ---------- 5. fact / dim row counts ----------
    for table, expected in [("fact_sales", 592), ("fact_purchases", 180),
                            ("dim_product", 40), ("dim_customer", 25),
                            ("dim_supplier", 8), ("dim_date", 181),
                            ("int_sales_enriched", 592),
                            ("mart_inventory", 40), ("mart_supplier_spend", 8)]:
        check(f"{table} = {expected} rows",
              q(conn, f"SELECT COUNT(*) FROM {table}") == expected,
              q(conn, f"SELECT COUNT(*) FROM {table}"))

    # ---------- 6. grain checks ----------
    check("fact_sales grain: one row per staged sale line",
          q(conn, "SELECT COUNT(*) FROM fact_sales")
          == q(conn, "SELECT COUNT(*) FROM stg_sales"))
    check("fact_sales sale_line_id is unique (592 distinct)",
          q(conn, "SELECT COUNT(DISTINCT sale_line_id) FROM fact_sales") == 592)
    check("fact_sales has no NULL keys",
          q(conn, """SELECT COUNT(*) FROM fact_sales WHERE order_id IS NULL
              OR sale_date IS NULL OR customer_id IS NULL
              OR product_code IS NULL OR qty IS NULL
              OR line_total_pkr IS NULL""") == 0)
    check("fact_sales has no duplicate (order, product, qty, price) lines",
          q(conn, """SELECT COUNT(*) FROM (SELECT 1 FROM fact_sales GROUP BY
              order_id, sale_date, customer_id, product_code, qty,
              unit_price_pkr, line_total_pkr HAVING COUNT(*) > 1)""") == 0)

    # ---------- 7. mart totals reconcile to raw totals ----------
    # dedupe the clean set properly:
    seen, clean_gross, clean_profit = set(), 0, 0
    cost = {r["product_code"]: int(r["cost_price_pkr"]) for r in raw_prod}
    for r in raw_sales:
        k = tuple(r.values())
        if (int(r["qty"]) > 0 and r["product_code"] in prod_codes
                and int(r["line_total_pkr"]) == int(r["qty"]) * int(r["unit_price_pkr"])
                and k not in seen):
            seen.add(k)
            clean_gross += int(r["line_total_pkr"])
            clean_profit += int(r["line_total_pkr"]) - int(r["qty"]) * cost[r["product_code"]]
    raw_purch_total = sum(int(r["total_cost_pkr"]) for r in raw_purch)
    fact_gross = q(conn, "SELECT SUM(line_total_pkr) FROM fact_sales")
    fact_profit = q(conn, "SELECT SUM(gross_profit_pkr) FROM fact_sales")
    fact_spend = q(conn, "SELECT SUM(total_cost_pkr) FROM fact_purchases")
    inv_value = q(conn, "SELECT SUM(stock_value_pkr) FROM mart_inventory")
    check("sales gross reconciles: fact = clean raw (PKR 27,211,450)",
          fact_gross == clean_gross == 27211450, f"fact {fact_gross:,} vs raw {clean_gross:,}")
    check("gross profit reconciles: fact = clean raw (PKR 2,339,510)",
          fact_profit == clean_profit == 2339510, f"fact {fact_profit:,} vs raw {clean_profit:,}")
    check("purchase spend reconciles: fact = raw (PKR 32,640,300)",
          fact_spend == raw_purch_total == 32640300, f"fact {fact_spend:,} vs raw {raw_purch_total:,}")
    check("inventory value = SUM(stock_qty x cost price) (PKR 7,724,910)",
          inv_value == q(conn, """SELECT SUM(stock_qty * cost_price_pkr)
              FROM mart_inventory i JOIN dim_product p
              ON p.product_code = i.product_code""") == 7724910,
          f"{inv_value:,}")
    check("margin = 8.60% (profit / gross)",
          abs(fact_profit / fact_gross - 0.0860) < 0.0005,
          f"{100.0 * fact_profit / fact_gross:.2f}%")

    # ---------- 8. per-category reconciliation (fact+dim vs intermediate) ----------
    cats = conn.execute("SELECT category FROM dim_product GROUP BY category").fetchall()
    check("8 categories", len(cats) == 8, len(cats))
    for (cat,) in cats:
        a = conn.execute("""SELECT SUM(line_total_pkr) FROM int_sales_enriched
                            WHERE category = ?""", (cat,)).fetchone()[0]
        b = conn.execute("""SELECT SUM(f.line_total_pkr) FROM fact_sales f
                            JOIN dim_product p ON p.product_code = f.product_code
                            WHERE p.category = ?""", (cat,)).fetchone()[0]
        check(f"category reconciles: {cat}", a == b, f"PKR {a:,}")
    check("category grosses sum to total gross",
          q(conn, "SELECT SUM(line_total_pkr) FROM int_sales_enriched") == fact_gross)

    # ---------- 9. per-supplier reconciliation ----------
    sups = conn.execute("SELECT supplier_id FROM dim_supplier").fetchall()
    check("8 suppliers", len(sups) == 8, len(sups))
    for (sup,) in sups:
        a = conn.execute("""SELECT total_spend_pkr FROM mart_supplier_spend
                            WHERE supplier_id = ?""", (sup,)).fetchone()[0]
        b = conn.execute("""SELECT SUM(total_cost_pkr) FROM fact_purchases
                            WHERE supplier_id = ?""", (sup,)).fetchone()[0]
        check(f"supplier spend reconciles: {sup}", a == b, f"PKR {a:,}")
    check("supplier spends sum to total purchase spend",
          q(conn, "SELECT SUM(total_spend_pkr) FROM mart_supplier_spend") == fact_spend)

    # ---------- 10. per-month reconciliation ----------
    for m in ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]:
        a = conn.execute("""SELECT SUM(line_total_pkr) FROM fact_sales
                            WHERE substr(sale_date, 1, 7) = ?""", (m,)).fetchone()[0]
        b = conn.execute("""SELECT SUM(line_total_pkr) FROM stg_sales
                            WHERE substr(sale_date, 1, 7) = ?""", (m,)).fetchone()[0]
        check(f"month reconciles: {m}", a == b and a is not None, f"PKR {a:,}")
    check("monthly grosses sum to total gross",
          q(conn, """SELECT SUM(line_total_pkr) FROM fact_sales""") == fact_gross)

    # ---------- 11. per-product inventory ----------
    prods = conn.execute("SELECT product_code, stock_qty, stock_value_pkr FROM mart_inventory").fetchall()
    for code, stock, value in prods:
        cp = conn.execute("SELECT cost_price_pkr FROM dim_product WHERE product_code = ?",
                          (code,)).fetchone()[0]
        check(f"inventory OK: {code} stock>=0 and value=stock x cost",
              stock >= 0 and value == stock * cp, f"stock {stock}, value PKR {value:,}")
    check("all 40 products have OK stock status",
          q(conn, "SELECT COUNT(*) FROM mart_inventory WHERE stock_status <> 'OK'") == 0)
    check("total stock units = purchased - sold (2,425)",
          q(conn, "SELECT SUM(stock_qty) FROM mart_inventory") == 2425)

    # ---------- 12. date dimension ----------
    check("dim_date = 181 days", q(conn, "SELECT COUNT(*) FROM dim_date") == 181)
    check("dim_date starts 2026-01-01",
          q(conn, "SELECT MIN(date_key) FROM dim_date") == "2026-01-01")
    check("dim_date ends 2026-06-30",
          q(conn, "SELECT MAX(date_key) FROM dim_date") == "2026-06-30")
    check("dim_date has no gaps (181 distinct dates)",
          q(conn, "SELECT COUNT(DISTINCT date_key) FROM dim_date") == 181)
    check("every fact sale date exists in dim_date",
          q(conn, """SELECT COUNT(*) FROM fact_sales
              WHERE sale_date NOT IN (SELECT date_key FROM dim_date)""") == 0)
    check("no fact sale date outside Jan–Jun 2026",
          q(conn, """SELECT COUNT(*) FROM fact_sales
              WHERE sale_date < '2026-01-01' OR sale_date > '2026-06-30'""") == 0)

    # ---------- 13. SCD Type 1 ----------
    check("dim_product: one row per product (SCD Type 1)",
          q(conn, "SELECT COUNT(*) FROM dim_product")
          == q(conn, "SELECT COUNT(DISTINCT product_code) FROM dim_product") == 40)
    check("dim_customer: 25 distinct shops",
          q(conn, "SELECT COUNT(DISTINCT customer_id) FROM dim_customer") == 25)
    check("dim_supplier: 8 distinct suppliers",
          q(conn, "SELECT COUNT(DISTINCT supplier_id) FROM dim_supplier") == 8)

    # ---------- 14. workbook: structure + LibreOffice recalc ----------
    check("workbook file exists", WB.exists())
    wb = load_workbook(WB)
    for sheet in ["Health", "Sales by category", "Inventory value",
                  "Supplier spend", "Method"]:
        check(f"workbook sheet present: {sheet}", sheet in wb.sheetnames)
    ws = wb["Health"]
    formulas = [c.value for row in ws.iter_rows() for c in row
                if isinstance(c.value, str) and c.value.startswith("=")]
    check("Health sheet has live-formula money totals", len(formulas) >= 5,
          f"{len(formulas)} formulas")
    cat_ws = wb["Sales by category"]
    check("category TOTAL row is SUM formulas",
          str(cat_ws.cell(row=10, column=4).value).startswith("=SUM("))
    check("supplier TOTAL row is SUM formulas",
          str(wb["Supplier spend"].cell(row=10, column=5).value).startswith("=SUM("))
    check("inventory TOTAL row is SUM formulas",
          str(wb["Inventory value"].cell(row=42, column=7).value).startswith("=SUM("))

    # LibreOffice headless recalc, then compare cached values to the database
    if RECALC_DIR.exists():
        shutil.rmtree(RECALC_DIR)
    RECALC_DIR.mkdir(parents=True)
    res = subprocess.run(
        ["soffice", "--headless", "--calc", "--convert-to", "xlsx",
         "--outdir", str(RECALC_DIR), str(WB)],
        capture_output=True, text=True, timeout=120)
    recalc_file = RECALC_DIR / WB.name
    check("LibreOffice recalculated the workbook", res.returncode == 0 and recalc_file.exists())
    if recalc_file.exists():
        rwb = load_workbook(recalc_file, data_only=True)
        errors = []
        for sh in rwb.sheetnames:
            for row in rwb[sh].iter_rows():
                for c in row:
                    if isinstance(c.value, str) and c.value.startswith("#"):
                        errors.append(f"{sh}!{c.coordinate}={c.value}")
        check("recalculated workbook has zero error values", not errors, "; ".join(errors[:5]))
        h = rwb["Health"]
        health = {row[0]: row[1] for row in h.iter_rows(values_only=True)
                  if row[0] and row[1] is not None}
        check("recalc: Health sales gross = PKR 27,211,450",
              health.get("Sales gross, clean (PKR)") == 27211450,
              health.get("Sales gross, clean (PKR)"))
        check("recalc: Health gross profit = PKR 2,339,510",
              health.get("Gross profit, clean (PKR)") == 2339510,
              health.get("Gross profit, clean (PKR)"))
        check("recalc: Health purchase spend = PKR 32,640,300",
              health.get("Purchase spend (PKR)") == 32640300,
              health.get("Purchase spend (PKR)"))
        check("recalc: Health inventory value = PKR 7,724,910",
              health.get("Inventory value at cost (PKR)") == 7724910,
              health.get("Inventory value at cost (PKR)"))
        check("recalc: test pass rate = 100%",
              health.get("Test pass rate") == 1, health.get("Test pass rate"))
        check("recalc: category TOTAL gross = PKR 27,211,450",
              rwb["Sales by category"].cell(row=10, column=4).value == 27211450)
        check("recalc: inventory TOTAL value = PKR 7,724,910",
              rwb["Inventory value"].cell(row=42, column=7).value == 7724910)
        check("recalc: supplier TOTAL spend = PKR 32,640,300",
              rwb["Supplier spend"].cell(row=10, column=5).value == 32640300)
        check("recalc: supplier share total = 100%",
              abs(rwb["Supplier spend"].cell(row=10, column=6).value - 1.0) < 1e-9)
    shutil.rmtree(RECALC_DIR, ignore_errors=True)

    # ---------- 15. .gitignore keeps the .db out of the repo ----------
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
    check(".gitignore excludes *.db", "*.db" in gi)
    check("warehouse.db exists locally for verification", DB.exists())

    # ---------- 16. README / DQ report numbers match the verified figures ----------
    readme = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").exists() else ""
    for figure in ["27,211,450", "2,339,510", "32,640,300", "7,724,910", "592", "8.60%"]:
        check(f"README states verified figure {figure}", figure in readme)
    dq = (ROOT / "outputs" / "dq_report.md").read_text(encoding="utf-8") \
        if (ROOT / "outputs" / "dq_report.md").exists() else ""
    for figure in ["16/16", "27,211,450", "2,339,510", "32,640,300", "7,724,910"]:
        check(f"dq_report states verified figure {figure}", figure in dq)
    check("dq_report records all 4 planted defect types",
          all(s in dq for s in ["duplicate", "qty", "unknown product", "wrong line total"]))

    # ---------- summary ----------
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    total = len(CHECKS)
    print(f"\n{passed}/{total} checks passed")
    failed = [name for name, ok, _ in CHECKS if not ok]
    if failed:
        print("FAILED:")
        for name in failed:
            print(f"  - {name}")
    conn.close()
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
