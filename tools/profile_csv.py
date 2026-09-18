"""Independent local reference calculation; does not execute the Snowflake models."""

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re


def profile(path):
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
    weekly = defaultdict(lambda: defaultdict(Decimal))
    dates, products = [], set()
    lines = mismatches = duplicate_product_orders = bad_emails = bad_phones = 0
    for row in rows:
        day = date.fromisoformat(row["order_date"])
        dates.append(day)
        week = str(day - timedelta(days=day.weekday()))
        items = json.loads(row["order_items"])
        lines += len(items)
        codes = [item["product_id"] for item in items]
        duplicate_product_orders += len(codes) != len(set(codes))
        total = Decimal(0)
        for item in items:
            amount = Decimal(str(item["quantity"])) * Decimal(str(item["price"]))
            total += amount
            weekly[week][item["product_id"]] += amount
            products.add(item["product_id"])
        mismatches += total != Decimal(row["order_total"])
        email = row["customer_email"].strip().lower()
        bad_emails += re.fullmatch(r"[a-z0-9._%+-]+@[a-z0-9.-]+[.][a-z]{2,}", email) is None
        phone = row["customer_phone"].replace('"', "").strip().upper()
        bad_phones += phone in ("", "N/A", "NULL", "123456")
    winners, ties = Counter(), 0
    for revenues in weekly.values():
        top = [code for code, amount in revenues.items() if amount == max(revenues.values())]
        winners.update(top)
        ties += len(top) > 1
    return {
        "verification": "local Python reference; not a Snowflake execution",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "orders": len(rows),
        "distinct_orders": len({row["order_id"] for row in rows}),
        "customers": len({row["customer_id"] for row in rows}),
        "products": len(products),
        "date_min": str(min(dates)), "date_max": str(max(dates)),
        "line_items": lines, "monday_weeks": len(weekly),
        "week_product_rows": sum(len(values) for values in weekly.values()),
        "exact_total_mismatches": mismatches,
        "duplicate_product_orders": duplicate_product_orders,
        "top_revenue_weeks": dict(sorted(winners.items())), "tied_weeks": ties,
        "invalid_emails": bad_emails, "phone_sentinels": bad_phones,
        "example_week_2024_05_27": {k: str(v) for k, v in sorted(weekly["2024-05-27"].items())},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", type=Path, default=Path("homework.csv"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(profile(args.file), indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
    print(result, end="")
