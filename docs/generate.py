"""Generate a deliberately messy synthetic manufacturing dataset."""
import os
import random
from datetime import date, timedelta

import duckdb
import pandas as pd

random.seed(42)

COUNTRIES = ["DE", "Germany", "Deutschland", "CZ", "Czechia",
             "PL", "Poland", "HU", "AT", "Austria"]
CATEGORIES = ["fastener", "casting", "electronics", "seal",
              "harness", "bearing", "sensor"]
MODELS = ["X1", "X3", "i4", "iX", "3-series", "5-series"]


def gen_suppliers(n=80):
    rows = []
    for i in range(1, n + 1):
        rows.append({
            "supplier_id": i,
            "name": f"Supplier {chr(65 + i % 26)}{i:03d}",
            "country": random.choice(COUNTRIES),
            "tier": random.choice([1, 1, 2, 2, 2, 3]),
            "onboarded_date": date(2018, 1, 1) + timedelta(days=random.randint(0, 2000)),
            "quality_rating": round(random.uniform(2.5, 5.0), 1),
        })
    # messiness: duplicate names, different IDs
    for j in range(4):
        rows.append({**rows[j], "supplier_id": n + j + 1,
                     "quality_rating": round(random.uniform(2.5, 5.0), 1)})
    return pd.DataFrame(rows)


def gen_parts(suppliers, n=400):
    ids = suppliers["supplier_id"].tolist()
    rows = []
    for i in range(1, n + 1):
        rows.append({
            "part_id": i,
            "part_number": f"BP-{random.randint(10000, 99999)}",
            "name": f"{random.choice(CATEGORIES)} {i}",
            "category": random.choice(CATEGORIES),
            "unit_cost": round(random.uniform(0.4, 950.0), 2),
            # messiness: some orphan foreign keys
            "supplier_id": random.choice(ids) if random.random() > 0.02 else 9999,
        })
    return pd.DataFrame(rows)


def gen_plants():
    return pd.DataFrame([
        {"plant_id": 1, "name": "Munich",     "city": "Munich",     "country": "DE"},
        {"plant_id": 2, "name": "Dingolfing", "city": "Dingolfing", "country": "Germany"},
        {"plant_id": 3, "name": "Leipzig",    "city": "Leipzig",    "country": "DE"},
        {"plant_id": 4, "name": "Regensburg", "city": "Regensburg", "country": "DE"},
        {"plant_id": 5, "name": "Steyr",      "city": "Steyr",      "country": "AT"},
        {"plant_id": 6, "name": "Debrecen",   "city": "Debrecen",   "country": "HU"},
    ])


def gen_orders(n=3000):
    rows = []
    for i in range(1, n + 1):
        start = date(2024, 1, 1) + timedelta(days=random.randint(0, 700))
        planned = random.randint(50, 5000)
        rows.append({
            "order_id": i,
            "plant_id": random.randint(1, 6),
            "model": random.choice(MODELS),
            "planned_qty": planned,
            "actual_qty": max(0, int(planned * random.uniform(0.75, 1.08))),
            "start_date": start,
            "end_date": start + timedelta(days=random.randint(3, 45)),
            # messiness: inconsistent casing
            "status": random.choice(["completed", "COMPLETED", "Completed",
                                     "cancelled", "in_progress"]),
        })
    return pd.DataFrame(rows)


def gen_consumption(orders, parts, n=40000):
    order_ids = orders["order_id"].tolist()
    part_ids = parts["part_id"].tolist()
    rows = []
    for i in range(1, n + 1):
        used = random.randint(1, 400)
        rows.append({
            "consumption_id": i,
            "order_id": random.choice(order_ids),
            "part_id": random.choice(part_ids),
            "qty_used": used,
            "scrap_qty": int(used * random.uniform(0, 0.09)),
        })
    return pd.DataFrame(rows)


def gen_deliveries(suppliers, parts, n=25000):
    sids = suppliers["supplier_id"].tolist()
    pids = parts["part_id"].tolist()
    rows = []
    for i in range(1, n + 1):
        promised = date(2024, 1, 1) + timedelta(days=random.randint(0, 730))
        late = random.random()
        if late < 0.06:
            actual = None                                     # not yet delivered
        elif late < 0.30:
            actual = promised + timedelta(days=random.randint(1, 21))
        else:
            actual = promised - timedelta(days=random.randint(0, 5))
        qty = random.randint(10, 2000)
        rows.append({
            "delivery_id": i,
            "supplier_id": random.choice(sids),
            "part_id": random.choice(pids),
            "plant_id": random.randint(1, 6),
            # messiness: dates stored as strings here
            "promised_date": promised.isoformat(),
            "actual_date": actual.isoformat() if actual else None,
            "qty": qty if random.random() > 0.004 else -qty,   # data-entry errors
            "qty_rejected": int(qty * random.uniform(0, 0.05)),
        })
    return pd.DataFrame(rows)


def gen_incidents(parts, n=1200):
    pids = parts["part_id"].tolist()
    rows = []
    for i in range(1, n + 1):
        reported = date(2024, 1, 1) + timedelta(days=random.randint(0, 730))
        resolved = reported + timedelta(days=random.randint(1, 90))
        rows.append({
            "incident_id": i,
            "part_id": random.choice(pids),
            "plant_id": random.randint(1, 6),
            "reported_date": reported,
            "severity": random.choice(["low", "medium", "high", "critical"]),
            "description": random.choice([
                "dimensional deviation", "surface defect", "material fatigue",
                "assembly misfit", "coating failure", "electrical fault"]),
            "resolved_date": resolved if random.random() > 0.15 else None,
        })
    return pd.DataFrame(rows)


def main(path="data/factory.duckdb"):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    suppliers = gen_suppliers()
    parts     = gen_parts(suppliers)
    plants    = gen_plants()
    orders    = gen_orders()
    cons      = gen_consumption(orders, parts)
    deliv     = gen_deliveries(suppliers, parts)
    inc       = gen_incidents(parts)

    con = duckdb.connect(path)
    for name, df in [("suppliers", suppliers), ("parts", parts),
                     ("plants", plants), ("production_orders", orders),
                     ("part_consumption", cons), ("deliveries", deliv),
                     ("quality_incidents", inc)]:
        con.execute(f"DROP TABLE IF EXISTS {name}")
        con.register("tmp_df", df)
        con.execute(f"CREATE TABLE {name} AS SELECT * FROM tmp_df")
        con.unregister("tmp_df")
        print(f"{name}: {len(df)} rows")
    con.close()


if __name__ == "__main__":
    main()