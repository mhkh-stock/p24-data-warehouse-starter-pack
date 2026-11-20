# P24 — Package Note (Fiverr-ready)

**Gig title:** I will build you a data warehouse starter pack from your sales and purchase files

**What the client gets:** a runnable data warehouse built from their
own CSVs — a star schema (sales + purchase facts, product / customer
/ supplier / date dimensions), dbt-style SQL models (staging,
intermediate, marts), 16 data-quality tests that catch duplicates,
negative quantities, unknown products and wrong totals, a
reconciliation report proving the money agrees from raw file to
fact table to workbook, and a live Excel health workbook (row
counts, test pass rate, sales by category, inventory value,
supplier spend — every total a formula). Delivered as a GitHub repo
they can re-run on next month's files themselves.

## Tiers (Hashir's band)

| Tier | Price | Delivery | Includes |
|---|---|---|---|
| Basic | $20 | 2 days | The warehouse on up to 3 source files (sales, purchases, products): star schema + staging models, the 16 data-quality tests with a pass/fail report, the health workbook with live formulas |
| Standard | $65 | 4 days | Everything in Basic + the 3 marts (sales, inventory, supplier spend), the full DQ report with every rejected line listed and its fix, sales by category / by month / by supplier tables, the reconciliation proof (raw → fact → workbook to the rupee) |
| Premium | $140 | 6 days | Everything in Standard + up to 6 source files (extra files: returns, expenses, staff, or a second branch), a second warehouse run on their next month's files to prove it re-runs, a 1-page owner guide (how to add a product, a supplier, a shop — and how to re-run the build), 1 revision round |

**What's NOT included:** running their business systems or talking
to their suppliers (they send their own CSV exports — quoted
separately if they need the exports pulled from their software);
changing their prices or product costs (this service shows them what
their own files say — the margin uses the cost price they give);
a live dashboard that updates itself (this service is a warehouse +
a workbook they re-run — a live dashboard is a different gig);
cleaning years of back-files (quoted separately by file count).

**Delivery time note:** counts from the day the client uploads
their 3 CSV exports (same columns as the sample), not from order
placement.

**Proof this service works:** this repo's SAMPLE — Khan Traders
(fictional Lahore wholesaler), 600 sale lines over 6 months,
PKR 27,211,450 clean sales gross, PKR 2,339,510 gross profit at
8.60% margin, PKR 32,640,300 purchase spend, PKR 7,724,910
inventory value, 241 orders across 25 shops, 8 planted defects
found exactly (2 duplicates, 3 qty ≤ 0, 2 unknown products,
1 wrong total), 16/16 data-quality tests passing, 100+ automated
checks passing including a LibreOffice recalculation of the
workbook with zero error values, biggest category Cooking Oil &
Ghee at PKR 5,510,600, biggest supplier Noor Oil Mills at
PKR 6,852,460 (20.99% of spend), and 3 recommendations the owner
can act on — fix the sales entry, watch the oil supplier, push the
high-margin categories.
