# P24 — Data Warehouse Starter Pack

**Client (SAMPLE):** Khan Traders — fictional wholesale distributor,
Lahore, 6 months (Thu 2026-01-01 → Tue 2026-06-30, 181 days) ·
**Status: SAMPLE delivery on DEMO data**
**Tools:** SQL (SQLite) · Python · Excel (live formulas)
**Deliverable:** `outputs/warehouse_health_SAMPLE.xlsx` +
`outputs/dq_report.md` — a runnable star-schema warehouse built from
the client's own CSVs

> ⚠️ **What this is and is not.** Khan Traders is a fictional
> distributor and the three source CSVs are demo data, generated to
> show the method. No real business, supplier or shop is involved.
> What is real is the warehouse: the same staging models, star
> schema, data-quality tests and reconciliation checks run on a real
> client's sales, purchase and product files the same way, and every
> number in the report is recomputed from the data, never typed.

## Business question it answers

> "A warehouse I can actually query — where is my money, what is
> sitting in stock, and who do I depend on?"

A distributor running on three spreadsheets cannot answer that: the
sales file has duplicate lines, negative quantities and products
that do not exist; nobody knows what is actually in stock; and the
biggest supplier's share is a guess. This delivery answers it with a
warehouse: clean sale and purchase facts, four dimensions, three
marts, 16 data-quality tests that all pass, and a health workbook
whose totals are live formulas — so the owner can ask the warehouse
a question and trust the answer.

## The method (plainly stated)

**Star schema:** `fact_sales` (one row per clean sale line) and
`fact_purchases` (one row per purchase-order line), joined to
`dim_product`, `dim_customer`, `dim_supplier` and `dim_date`.
Staging models (`stg_*`) clean the raw files; the intermediate
model (`int_sales_enriched`) joins sales to the product master and
adds the economics; the marts (`mart_sales`, `mart_inventory`,
`mart_supplier_spend`) are the tables the business queries.

**Gross profit = line total − qty × cost price.** Cost price is the
product master's standard cost, not the per-PO unit cost (which
moves ±3% around it) — so profit is the margin on the price list,
not on each individual purchase. **Margin % = gross profit / gross
sales = 8.60%** — a wholesale margin: thin, high volume.

**Inventory value = stock qty × cost price**, where stock qty =
purchased qty − sold qty. **Stock status rule, stated:** stock below
10% of what was bought in the period is LOW; zero or less is OUT.
All 40 products are OK in this sample.

**Supplier share % = supplier spend / total purchase spend.**
Noor Oil Mills is the biggest at 20.99% — the supplier whose
failure would hurt most.

**The 8 rejected lines:** 2 duplicates, 3 qty ≤ 0, 2 unknown
products (PRD-999, PRD-888), 1 wrong line total (PKR 500 too high).
They are rejected by the staging models, never silently fixed, and
the raw file is untouched — see `outputs/dq_report.md` for the line
numbers and the fix for each one. Raw gross PKR 27,321,100 minus
rejected PKR 109,650 = clean gross PKR 27,211,450, exactly what the
fact table holds.

**SCD policy, stated:** `dim_product` is Type 1 — one row per
product, overwritten when a price changes. No price history is kept.
If the client later needs history, the dimension becomes Type 2
(`valid_from` / `valid_to`) and only the loader changes.

**Limits, stated upfront:** the customer and supplier masters are
small reference lists loaded from SQL (`sql/load_dimensions.sql`),
not CSVs, because the client keeps them outside the transaction
exports. Every purchase order has exactly one line in this sample,
so `po_count` and `po_lines` are the same number (180) — on a real
file with multi-line POs they will differ, and the mart counts them
separately. January is the best month and February the weakest in
this sample — that is the sample's own seasonality, not a finding
about the real market.

## What is inside

| File | What it does |
|---|---|
| `outputs/warehouse_health_SAMPLE.xlsx` | The deliverable: Health (row counts + test pass rate + money totals as live formulas) + Sales by category + Inventory value + Supplier spend + Method |
| `outputs/dq_report.md` | Findings report: 16/16 test results, every defect with its fix, reconciliation |
| `outputs/test_results.json` | Machine-readable test results (16 tests) |
| `data/raw/sales_SAMPLE.csv` | The sales file: 600 lines, 592 clean + 8 planted defects |
| `data/raw/purchases_SAMPLE.csv` | The purchase file: 180 lines, 8 suppliers, 40 products |
| `data/raw/products_SAMPLE.csv` | The product master: 40 products, 8 categories |
| `data/processed/warehouse.db` | The built warehouse (SQLite — NOT committed; rebuilds from the scripts) |
| `data/processed/fact_sales.csv` | The fact table as a CSV (592 rows) |
| `data/processed/mart_inventory.csv` | Stock on hand per product (40 rows) |
| `data/processed/mart_supplier_spend.csv` | Spend per supplier (8 rows) |
| `data/README.md` | Data dictionary + planted defects + known quirks |
| `sql/schema.sql` | Star schema DDL: 2 facts + 4 dimensions + 3 raw landing tables |
| `sql/stg_sales.sql`, `stg_purchases.sql`, `stg_products.sql` | Staging models (cleaning + rejection guards) |
| `sql/int_sales_enriched.sql` | Intermediate model (joins + COGS + gross profit + margin) |
| `sql/load_dimensions.sql` | Dimension loads + date dimension (181 days) |
| `sql/mart_sales.sql`, `mart_inventory.sql`, `mart_supplier_spend.sql` | Mart models (facts + stock + supplier spend) |
| `sql/tests/` | 16 data-quality test queries (uniqueness, not-null, referential integrity, reconciliation, stale dates) |
| `src/generate_data.py` | Makes the SAMPLE files (seed 20261120; NOT run on a real client file) |
| `src/build_warehouse.py` | Runs schema + models in order into `warehouse.db`, prints row counts |
| `src/run_tests.py` | Runs all 16 tests, prints PASS/FAIL per test + summary |
| `src/build_workbook.py` | Builds the workbook: 5 sheets, live formulas |
| `src/checks.py` | Verification suite — 100+ checks, all passing (incl. LibreOffice recalc) |
| `requirements.txt` | Pinned: `openpyxl==3.1.2` (Python 3.12) |

## How it fits together

```
Client CSVs (sales, purchases, products) ──▶ raw_* tables ──▶ stg_* models
   (600 / 180 / 40 rows in the demo)              (8 bad lines rejected)
                                                        ▼
                                              int_sales_enriched ──▶ fact_sales
                                              load_dimensions ──▶ dim_* (4 dims)
                                                        ▼
                                              mart_inventory + mart_supplier_spend
                                                        ▼
                                              src/build_workbook.py ──▶ warehouse_health_SAMPLE.xlsx
                                                        ▲ src/checks.py verifies all of it (100+ checks)
```

## Headline numbers (SAMPLE — Khan Traders, 6 months)

- **592 clean sale lines · 241 orders · 25 customer shops ·
  7,930 units sold** · **sales gross PKR 27,211,450** · **gross
  profit PKR 2,339,510** · **margin 8.60%**
- **180 purchase lines · 8 suppliers · 10,355 units bought** ·
  **purchase spend PKR 32,640,300**
- **Inventory value at cost: PKR 7,724,910** — 2,425 units in stock
  across 40 products, all OK (0 LOW, 0 OUT)
- **16/16 data-quality tests passing** · **8 raw lines rejected**
  (2 duplicates, 3 qty ≤ 0, 2 unknown products, 1 wrong total)
- **Biggest category: Cooking Oil & Ghee (PKR 5,510,600)**; biggest
  supplier: **Noor Oil Mills (PKR 6,852,460, 20.99% of spend)**;
  best month: **January (PKR 5,881,460)**; weakest: **February
  (PKR 3,159,800)**
- **Top product: Cooking Oil (16 L tin) — PKR 1,869,000**; top
  customer: **Khan General Store (Ravi Road) — PKR 2,068,240**

## Sales by category

| Category | Lines | Units | Gross sales | Gross profit | Margin |
|---|---|---|---|---|---|
| Cooking Oil & Ghee | 85 | 995 | PKR 5,510,600 | PKR 382,950 | 6.95% |
| Pulses & Lentils | 104 | 1,063 | PKR 4,722,380 | PKR 406,730 | 8.61% |
| Tea & Beverages | 69 | 945 | PKR 3,988,220 | PKR 349,020 | 8.75% |
| Spices & Masala | 86 | 1,066 | PKR 3,489,930 | PKR 333,680 | 9.56% |
| Rice & Grains | 76 | 649 | PKR 3,256,350 | PKR 288,650 | 8.86% |
| Flour & Atta | 67 | 1,484 | PKR 2,267,610 | PKR 227,340 | 10.03% |
| Sugar & Sweeteners | 54 | 799 | PKR 2,007,660 | PKR 153,010 | 7.62% |
| Household & Cleaning | 51 | 929 | PKR 1,968,700 | PKR 198,130 | 10.06% |
| **TOTAL** | **592** | **7,930** | **PKR 27,211,450** | **PKR 2,339,510** | **8.60%** |

Flour & Atta moves the most units (1,484) at the lowest ticket;
Cooking Oil & Ghee brings the most rupees (PKR 5,510,600) on the
fewest units per rupee. Spices & Masala and Household & Cleaning
carry the best margins (9.56% and 10.06%); Cooking Oil & Ghee the
thinnest (6.95%) — the category that earns the most also earns the
least per rupee.

## Supplier spend

| Supplier | POs | Products | Total spend | Share |
|---|---|---|---|---|
| Noor Oil Mills | 27 | 6 | PKR 6,852,460 | 20.99% |
| Lahore Pulses Traders | 32 | 7 | PKR 5,554,250 | 17.02% |
| Chaman Tea Traders | 18 | 4 | PKR 4,529,670 | 13.88% |
| Shahi Masala Traders | 27 | 6 | PKR 4,320,830 | 13.24% |
| Punjab Rice Mills | 23 | 5 | PKR 3,986,720 | 12.21% |
| Al-Noor Flour Mills | 22 | 5 | PKR 2,739,300 | 8.39% |
| Ravi Sugar Traders | 18 | 4 | PKR 2,500,280 | 7.66% |
| City Household Distributors | 13 | 3 | PKR 2,156,790 | 6.61% |
| **TOTAL** | **180** | **40** | **PKR 32,640,300** | **100.00%** |

The top two suppliers take 38.01% of all spend. Noor Oil Mills
alone is a fifth of the money — the dependency to watch first.

## Month by month

| Month | Lines | Units | Gross sales | Gross profit |
|---|---|---|---|---|
| 2026-01 | 125 | 1,711 | PKR 5,881,460 | PKR 499,960 |
| 2026-02 | 72 | 986 | PKR 3,159,800 | PKR 283,940 |
| 2026-03 | 89 | 1,123 | PKR 3,909,120 | PKR 325,170 |
| 2026-04 | 121 | 1,519 | PKR 5,553,480 | PKR 470,860 |
| 2026-05 | 100 | 1,351 | PKR 4,688,270 | PKR 407,480 |
| 2026-06 | 85 | 1,240 | PKR 4,019,320 | PKR 352,100 |
| **TOTAL** | **592** | **7,930** | **PKR 27,211,450** | **PKR 2,339,510** |

## The three recommendations (from the data, not from a template)

1. **Fix the sales file before anything else: 8 of 600 lines (1.3%)
   are wrong — duplicates, negative quantities, products that do not
   exist, and a total PKR 500 too high.** The warehouse already
   rejects them, but the source file keeps producing them. Whoever
   types the sales must get a product list to pick from (no free
   typing of product codes) and the sheet must compute the line
   total itself — that alone removes 3 of the 4 defect types.
2. **Watch the Noor Oil Mills dependency: PKR 6,852,460 — 20.99% of
   all purchase spend — goes to one supplier, and Cooking Oil &
   Ghee is both the biggest sales category (PKR 5,510,600) and the
   thinnest margin (6.95%).** If that supplier raises prices or
   fails to deliver, the biggest revenue line is the one that
   hurts. Line up a second oil supplier before the next quarter.
3. **Push the high-margin categories: Spices & Masala (9.56%) and
   Household & Cleaning (10.06%) earn the best margin per rupee
   but sit 4th and 8th by sales.** They are the categories where an
   extra rupee of sales keeps the most profit — worth a push to the
   shops that already buy them, before chasing more low-margin oil
   volume.

## Same logic, two ways — and they must agree

The headline numbers exist in two forms: the SQL in `sql/` and the
workbook's formulas. `src/checks.py` runs both against the raw files
and compares them — a mistake in either one shows up as a failure.
The workbook's formulas were also recalculated in LibreOffice: every
total matches the recompute exactly, with zero error values.

## Reproduce it (2 minutes)

```bash
python3 src/generate_data.py    # rebuild the SAMPLE files (seed 20261120)
python3 src/build_warehouse.py  # schema + models → data/processed/warehouse.db
python3 src/run_tests.py        # 16 tests — expect 16/16 passing
python3 src/build_workbook.py   # outputs/warehouse_health_SAMPLE.xlsx
python3 src/checks.py           # 100+ checks — expect all passing
```

On a real client file, replace the three CSVs in `data/raw/` with the
client's exports (same columns) and skip `generate_data.py` — add the
client's customer and supplier lists to `sql/load_dimensions.sql` and
everything downstream runs unchanged. The `.db` file is never
committed; it rebuilds from the scripts.
