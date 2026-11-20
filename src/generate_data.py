"""Generate the SAMPLE source files for P24 — Khan Traders (SAMPLE client).

Seeded (seed 20261120) so the same files regenerate exactly.
Writes data/raw/products_SAMPLE.csv, sales_SAMPLE.csv, purchases_SAMPLE.csv.

The sales file deliberately contains 8 planted defects so the data-quality
tests have something real to catch (recorded in data/README.md):
  * 2 exact duplicate lines
  * 3 lines with qty <= 0
  * 2 lines referencing an unknown product (PRD-999, PRD-888)
  * 1 line with a wrong line total (off by PKR 500)
Valid sales lines: 592. Raw sales lines total: 600.
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20261120
rng = random.Random(SEED)

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

SUPPLIERS = [
    ("SUP-01", "Punjab Rice Mills", "Gujranwala"),
    ("SUP-02", "Al-Noor Flour Mills", "Lahore"),
    ("SUP-03", "Ravi Sugar Traders", "Faisalabad"),
    ("SUP-04", "Noor Oil Mills", "Lahore"),
    ("SUP-05", "Lahore Pulses Traders", "Akbari Mandi, Lahore"),
    ("SUP-06", "Shahi Masala Traders", "Lahore"),
    ("SUP-07", "Chaman Tea Traders", "Lahore"),
    ("SUP-08", "City Household Distributors", "Lahore"),
]

# code, name, category, supplier, unit, cost_price, sell_price (PKR)
PRODUCTS = [
    ("PRD-001", "Basmati Rice 1121 (25 kg bag)", "Rice & Grains", "SUP-01", "25 kg bag", 7200, 7850),
    ("PRD-002", "Basmati Rice Super Kernel (25 kg bag)", "Rice & Grains", "SUP-01", "25 kg bag", 6800, 7400),
    ("PRD-003", "Irri Rice (25 kg bag)", "Rice & Grains", "SUP-01", "25 kg bag", 3900, 4300),
    ("PRD-004", "Broken Rice (25 kg bag)", "Rice & Grains", "SUP-01", "25 kg bag", 2900, 3200),
    ("PRD-005", "Brown Rice (10 kg bag)", "Rice & Grains", "SUP-01", "10 kg bag", 3100, 3450),
    ("PRD-006", "Chakki Atta (10 kg bag)", "Flour & Atta", "SUP-02", "10 kg bag", 1150, 1280),
    ("PRD-007", "Chakki Atta (20 kg bag)", "Flour & Atta", "SUP-02", "20 kg bag", 2250, 2480),
    ("PRD-008", "Fine Maida (10 kg bag)", "Flour & Atta", "SUP-02", "10 kg bag", 1250, 1390),
    ("PRD-009", "Besan / Gram Flour (5 kg bag)", "Flour & Atta", "SUP-02", "5 kg bag", 980, 1100),
    ("PRD-010", "Suji / Semolina (5 kg bag)", "Flour & Atta", "SUP-02", "5 kg bag", 720, 820),
    ("PRD-011", "White Sugar (50 kg bag)", "Sugar & Sweeteners", "SUP-03", "50 kg bag", 7800, 8300),
    ("PRD-012", "White Sugar (10 kg bag)", "Sugar & Sweeteners", "SUP-03", "10 kg bag", 1620, 1750),
    ("PRD-013", "Brown Sugar / Shakkar (5 kg)", "Sugar & Sweeteners", "SUP-03", "5 kg", 890, 1010),
    ("PRD-014", "Gur / Jaggery (5 kg)", "Sugar & Sweeteners", "SUP-03", "5 kg", 760, 880),
    ("PRD-015", "Cooking Oil (16 L tin)", "Cooking Oil & Ghee", "SUP-04", "16 L tin", 9850, 10500),
    ("PRD-016", "Cooking Oil (5 L)", "Cooking Oil & Ghee", "SUP-04", "5 L", 3150, 3400),
    ("PRD-017", "Cooking Oil (1 L x 12 pack)", "Cooking Oil & Ghee", "SUP-04", "pack of 12", 6900, 7350),
    ("PRD-018", "Banaspati Ghee (16 kg tin)", "Cooking Oil & Ghee", "SUP-04", "16 kg tin", 9200, 9850),
    ("PRD-019", "Banaspati Ghee (5 kg)", "Cooking Oil & Ghee", "SUP-04", "5 kg", 2950, 3200),
    ("PRD-020", "Mustard Oil (5 L)", "Cooking Oil & Ghee", "SUP-04", "5 L", 2650, 2900),
    ("PRD-021", "Chana Dal (25 kg bag)", "Pulses & Lentils", "SUP-05", "25 kg bag", 5400, 5900),
    ("PRD-022", "Masoor Dal (25 kg bag)", "Pulses & Lentils", "SUP-05", "25 kg bag", 6100, 6650),
    ("PRD-023", "Moong Dal (25 kg bag)", "Pulses & Lentils", "SUP-05", "25 kg bag", 5800, 6350),
    ("PRD-024", "Mash Dal (10 kg bag)", "Pulses & Lentils", "SUP-05", "10 kg bag", 2900, 3180),
    ("PRD-025", "Arhar / Toor Dal (10 kg bag)", "Pulses & Lentils", "SUP-05", "10 kg bag", 2750, 3020),
    ("PRD-026", "White Chana (25 kg bag)", "Pulses & Lentils", "SUP-05", "25 kg bag", 6900, 7500),
    ("PRD-027", "Red Beans / Lobia (10 kg bag)", "Pulses & Lentils", "SUP-05", "10 kg bag", 2450, 2700),
    ("PRD-028", "Red Chilli Powder (5 kg)", "Spices & Masala", "SUP-06", "5 kg", 3400, 3750),
    ("PRD-029", "Turmeric Powder (5 kg)", "Spices & Masala", "SUP-06", "5 kg", 2100, 2350),
    ("PRD-030", "Coriander Powder (5 kg)", "Spices & Masala", "SUP-06", "5 kg", 1850, 2080),
    ("PRD-031", "Garam Masala (5 kg)", "Spices & Masala", "SUP-06", "5 kg", 4200, 4600),
    ("PRD-032", "Cumin Seeds (5 kg)", "Spices & Masala", "SUP-06", "5 kg", 5200, 5650),
    ("PRD-033", "Black Pepper (1 kg)", "Spices & Masala", "SUP-06", "1 kg", 2950, 3300),
    ("PRD-034", "Black Tea (10 kg)", "Tea & Beverages", "SUP-07", "10 kg", 8800, 9500),
    ("PRD-035", "Black Tea (5 kg)", "Tea & Beverages", "SUP-07", "5 kg", 4500, 4900),
    ("PRD-036", "Green Tea (1 kg)", "Tea & Beverages", "SUP-07", "1 kg", 2400, 2680),
    ("PRD-037", "Tea Whitener (5 kg)", "Tea & Beverages", "SUP-07", "5 kg", 3100, 3400),
    ("PRD-038", "Washing Powder (10 kg)", "Household & Cleaning", "SUP-08", "10 kg", 2350, 2600),
    ("PRD-039", "Dishwash Bar (pack of 12)", "Household & Cleaning", "SUP-08", "pack of 12", 1150, 1300),
    ("PRD-040", "Bath Soap (pack of 24)", "Household & Cleaning", "SUP-08", "pack of 24", 1980, 2200),
]

CUSTOMERS = [
    ("CUS-01", "Bilal General Store", "Shah Alam Market"),
    ("CUS-02", "Al-Madina Karyana Store", "Akbari Mandi"),
    ("CUS-03", "Usman Traders", "Urdu Bazaar"),
    ("CUS-04", "Haji Sons General Store", "Ichhra"),
    ("CUS-05", "Rehman Karyana", "Township"),
    ("CUS-06", "Al-Falah Store", "Gulberg III"),
    ("CUS-07", "Chaudhry General Store", "Model Town"),
    ("CUS-08", "Zain Traders", "Johar Town"),
    ("CUS-09", "Bismillah Karyana", "Samanabad"),
    ("CUS-10", "Noor General Store", "DHA Phase 4"),
    ("CUS-11", "Ahmad Cash & Carry", "Wahdat Road"),
    ("CUS-12", "Ghulam Rasool & Sons", "Badami Bagh"),
    ("CUS-13", "Shahzad Super Store", "Faisal Town"),
    ("CUS-14", "Al-Habib Karyana", "Green Town"),
    ("CUS-15", "Malik General Store", "Sabzazar"),
    ("CUS-16", "Rana Traders", "Cavalry Ground"),
    ("CUS-17", "Imran Store", "Mughalpura"),
    ("CUS-18", "Siddique General Store", "Shadbagh"),
    ("CUS-19", "Al-Rehman Cash & Carry", "Allama Iqbal Town"),
    ("CUS-20", "Khan General Store", "Ravi Road"),
    ("CUS-21", "Farooq Karyana Store", "Bhatti Gate"),
    ("CUS-22", "Naseer Traders", "Misri Shah"),
    ("CUS-23", "Tariq Super Store", "Wapda Town"),
    ("CUS-24", "Al-Noor General Store", "Cantt"),
    ("CUS-25", "Hassan Cash & Carry", "Gulshan-e-Ravi"),
]

START = date(2026, 1, 1)
END = date(2026, 6, 30)
DAYS = (END - START).days + 1  # 181


def rand_date():
    return START + timedelta(days=rng.randrange(DAYS))


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main():
    RAW.mkdir(parents=True, exist_ok=True)

    # --- products ---
    write_csv(
        RAW / "products_SAMPLE.csv",
        ["product_code", "product_name", "category", "supplier_id", "unit",
         "cost_price_pkr", "sell_price_pkr"],
        [[c, n, cat, s, u, cp, sp] for (c, n, cat, s, u, cp, sp) in PRODUCTS],
    )

    # --- valid sales: 592 lines across ~240 orders ---
    prod_by_code = {p[0]: p for p in PRODUCTS}
    valid = []
    order_no = 0
    lines_left = 592
    while lines_left > 0:
        order_no += 1
        n_lines = min(rng.randint(1, 4), lines_left)
        lines_left -= n_lines
        oid = f"ORD-{order_no:04d}"
        d = rand_date()
        cust = rng.choice(CUSTOMERS)[0]
        chosen = rng.sample(PRODUCTS, n_lines)
        for p in chosen:
            qty = rng.randint(2, 40) if p[6] < 3000 else rng.randint(2, 15)
            unit_price = p[6]
            valid.append([oid, d.isoformat(), cust, p[0], qty, unit_price,
                          qty * unit_price])
    valid.sort(key=lambda r: (r[1], r[0]))

    # --- planted defects (8 lines) ---
    defects = []
    # 2 exact duplicates of valid lines
    for row in rng.sample(valid, 2):
        defects.append(list(row))
    # 3 lines with qty <= 0
    for qty in (0, -1, -2):
        p = rng.choice(PRODUCTS)
        d = rand_date()
        cust = rng.choice(CUSTOMERS)[0]
        defects.append([f"ORD-{order_no + 1:04d}", d.isoformat(), cust,
                        p[0], qty, p[6], qty * p[6]])
        order_no += 1
    # 2 lines referencing an unknown product
    for code in ("PRD-999", "PRD-888"):
        d = rand_date()
        cust = rng.choice(CUSTOMERS)[0]
        defects.append([f"ORD-{order_no + 1:04d}", d.isoformat(), cust,
                        code, 5, 1000, 5000])
        order_no += 1
    # 1 line with a wrong line total (off by PKR 500)
    p = rng.choice(PRODUCTS)
    qty = rng.randint(3, 10)
    defects.append([f"ORD-{order_no + 1:04d}", rand_date().isoformat(),
                    rng.choice(CUSTOMERS)[0], p[0], qty, p[6],
                    qty * p[6] + 500])

    raw_sales = valid + defects
    # insert defects at random positions so they are not all at the end
    rng.shuffle(raw_sales)
    write_csv(
        RAW / "sales_SAMPLE.csv",
        ["order_id", "sale_date", "customer_id", "product_code", "qty",
         "unit_price_pkr", "line_total_pkr"],
        raw_sales,
    )

    # --- purchases: 180 lines, per-product purchased qty >= sold qty ---
    sold_qty = {}
    for row in valid:
        sold_qty[row[3]] = sold_qty.get(row[3], 0) + row[4]
    purchases = []
    po_no = 0
    for i, p in enumerate(PRODUCTS):
        n_pos = 5 if i % 2 == 0 else 4  # 20*5 + 20*4 = 180
        target = int(sold_qty[p[0]] * rng.uniform(1.15, 1.45))
        # split target across POs, each at least 1
        cuts = sorted(rng.sample(range(1, target), n_pos - 1)) if target > n_pos else list(range(1, n_pos))
        parts, prev = [], 0
        for c in cuts + [target]:
            parts.append(c - prev)
            prev = c
        for qty in parts:
            po_no += 1
            unit_cost = int(round(p[5] * rng.uniform(0.97, 1.03) / 10.0) * 10)
            purchases.append([f"PO-{po_no:04d}", rand_date().isoformat(),
                              p[3], p[0], qty, unit_cost, qty * unit_cost])
    purchases.sort(key=lambda r: (r[1], r[0]))
    write_csv(
        RAW / "purchases_SAMPLE.csv",
        ["po_id", "purchase_date", "supplier_id", "product_code", "qty",
         "unit_cost_pkr", "total_cost_pkr"],
        purchases,
    )

    print(f"products: {len(PRODUCTS)}")
    print(f"sales raw: {len(raw_sales)} (valid {len(valid)} + defects {len(defects)})")
    print(f"purchases: {len(purchases)}")
    print(f"sold qty check: min purchase/sold ratio per product = "
          f"{min(sum(r[4] for r in purchases if r[3] == p[0]) / sold_qty[p[0]] for p in PRODUCTS):.2f}")


if __name__ == "__main__":
    main()
