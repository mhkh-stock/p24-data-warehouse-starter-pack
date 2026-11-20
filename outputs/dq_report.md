# P24 — Data Quality Report (Khan Traders, SAMPLE)

**Period:** Thu 2026-01-01 → Tue 2026-06-30 (181 days) · **Warehouse:**
`data/processed/warehouse.db` (SQLite, rebuildable) ·
**Tests:** 16/16 passing · **Checks:** see `src/checks.py`

## Headline numbers (all verified — see `src/checks.py`)

- **600 raw sale lines in, 592 clean lines out** — 8 lines rejected
  (1.3% of the file), all 8 planted defects found exactly.
- **Sales gross (clean): PKR 27,211,450** · **gross profit:
  PKR 2,339,510** · **margin 8.60%** (wholesale margin — thin, high volume).
- **Purchase spend: PKR 32,640,300** across 180 purchase-order lines
  from 8 suppliers.
- **Inventory value at cost: PKR 7,724,910** — 2,425 units in stock
  across 40 products; every product in stock (0 LOW, 0 OUT).
- **241 orders · 25 customer shops · 7,930 units sold · 10,355 units
  bought.**

## Test results — 16/16 passing

| # | Test | What it checks | Result |
|---|---|---|---|
| t01 | raw duplicate lines | exactly 2 duplicate lines in the raw file | PASS |
| t02 | raw non-positive qty | exactly 3 lines with qty ≤ 0 | PASS |
| t03 | raw unknown product | exactly 2 lines with an unknown product | PASS |
| t04 | raw wrong line total | exactly 1 line with a wrong total | PASS |
| t05 | staging: no duplicates | no duplicate line survives into staging | PASS |
| t06 | staging: positive qty | every staged line has qty > 0 | PASS |
| t07 | staging: product exists | every staged line references a known product | PASS |
| t08 | staging: totals correct | every staged line total = qty × unit price | PASS |
| t09 | fact grain | fact_sales has one row per staged sale line (592) | PASS |
| t10 | fact: no NULL keys | no NULL order / date / customer / product / qty / total | PASS |
| t11 | fact totals reconcile | fact gross = staged gross (PKR 27,211,450) | PASS |
| t12 | dim_date coverage | 181 days, 2026-01-01 … 2026-06-30, no gaps | PASS |
| t13 | dim_product SCD Type 1 | exactly one row per product (40) | PASS |
| t14 | fact: no stale dates | no sale date outside Jan–Jun 2026 | PASS |
| t15 | inventory non-negative | no product below zero stock | PASS |
| t16 | purchase totals reconcile | fact spend = staged spend (PKR 32,640,300) | PASS |

Every test is a SQL file in `sql/tests/` — it returns its violating
rows, so 0 rows means PASS. Re-run any time with
`python3 src/run_tests.py` (writes `outputs/test_results.json`).

## What each defect was — and what happened to it

All 8 defective lines were rejected by the staging models
(`sql/stg_sales.sql`). Nothing was silently fixed; the raw file is
untouched in `data/raw/`, and the rejected lines can be found again
by their `raw_line_no`.

| Defect | Raw lines | What was wrong | Fix applied |
|---|---|---|---|
| Duplicate lines (2) | 30 & 391; 441 & 598 | Same line entered twice: ORD-0095 / PRD-035 / qty 12 / PKR 58,800, and ORD-0206 / PRD-003 / qty 8 / PKR 34,400 | Staging keeps the first occurrence (lowest `raw_line_no`); the copy is dropped. If these were two real deliveries, the client must confirm — duplicates are dropped, never merged. |
| qty ≤ 0 (3) | 37, 48, 338 | ORD-0243 / PRD-039 qty −1 (PKR −1,300); ORD-0244 / PRD-021 qty −2 (PKR −11,800); ORD-0242 / PRD-016 qty 0 (PKR 0) | Rejected. A negative quantity is a return, not a sale — returns belong in their own file with their own reason code, not as negative sale lines. |
| Unknown product (2) | 215, 297 | ORD-0246 references PRD-888; ORD-0245 references PRD-999. Neither code exists in the product master. | Rejected. The product must be added to the master first (name, category, cost, sell price) — then the line loads on the next run. |
| Wrong line total (1) | 175 | ORD-0247 / PRD-023, qty 3 × PKR 6,350 = PKR 19,050, but recorded as PKR 19,550 (PKR 500 too high) | Rejected. The total is recomputed from qty × unit price on load, so a typed total can never reach the fact table. |

**Reconciliation:** raw gross PKR 27,321,100 − rejected lines
PKR 109,650 (duplicates PKR 93,200; bad quantities PKR −13,100;
unknown products PKR 10,000; wrong total PKR 19,550) = clean gross
PKR 27,211,450, which is exactly what `fact_sales` holds. The
workbook's Health sheet shows the same totals from live formulas,
recalculated in LibreOffice with zero error values.

## What the warehouse proves about the data

- **The grain holds:** 592 staged lines → 592 fact rows, one per
  sale line, no NULL keys, no duplicates left.
- **The money reconciles at every step:** raw → staging → fact →
  workbook, all four agree to the rupee (PKR 27,211,450 sales,
  PKR 32,640,300 purchases, PKR 7,724,910 inventory).
- **The calendar is complete:** 181 days with no gaps, and no sale
  falls outside the period.
- **Stock is honest:** purchases cover sales for every product, so
  no product shows negative stock — a negative stock here would
  mean the load is wrong, not the business.
- **The dimension is Type 1:** one row per product, so a price
  change overwrites the old price. History is not kept — see
  `data/README.md` for the Type 2 upgrade path.

## How to re-run

```bash
python3 src/build_warehouse.py   # rebuild warehouse.db + processed CSVs
python3 src/run_tests.py         # 16 tests — expect 16/16 passing
python3 src/build_workbook.py    # rebuild outputs/warehouse_health_SAMPLE.xlsx
python3 src/checks.py            # full verification suite — expect 0 failures
```
