#!/usr/bin/env python3
"""Independently recalculate and compare daily_by_sku.csv with sales.csv."""

import csv
from collections import defaultdict
from pathlib import Path


INPUT_FILE = Path("sales.csv")
RESULT_FILE = Path("daily_by_sku.csv")
EXPECTED_HEADER = ["sku", "order_date", "orders", "revenue"]


def normalize_status(value: str) -> str:
    status = value.strip().lower()
    return "cancelled" if status == "canceled" else status


def main() -> None:
    orders_seen = set()
    totals = defaultdict(lambda: {"orders": 0, "revenue": 0})

    with INPUT_FILE.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required_columns = {"order_id", "order_date", "sku", "quantity", "price", "status"}
        if not required_columns.issubset(reader.fieldnames or []):
            raise ValueError(f"В {INPUT_FILE} отсутствуют обязательные столбцы")

        for row in reader:
            order_id = row["order_id"].strip()
            if order_id in orders_seen:
                continue
            orders_seen.add(order_id)

            sku = row["sku"].strip()
            order_date = row["order_date"].strip()
            group = totals[(sku, order_date)]
            group["orders"] += 1

            if normalize_status(row["status"]) == "delivered":
                # Пустое или нечисловое количество трактуем как 0, как в
                # независимом контрольном расчёте.
                try:
                    quantity = int(row["quantity"].strip())
                except ValueError:
                    quantity = 0
                price = int(row["price"].strip())
                group["revenue"] += quantity * price

    expected_rows = [
        [sku, order_date, str(values["orders"]), str(values["revenue"])]
        for (sku, order_date), values in sorted(totals.items())
    ]

    with RESULT_FILE.open(encoding="utf-8-sig", newline="") as result_file:
        reader = csv.reader(result_file)
        header = next(reader, [])
        if header != EXPECTED_HEADER:
            raise AssertionError(f"Неверные заголовки: {header!r}")
        actual_rows = list(reader)

    if actual_rows != expected_rows:
        first_difference = next(
            (
                index
                for index, (actual, expected) in enumerate(zip(actual_rows, expected_rows), start=1)
                if actual != expected
            ),
            min(len(actual_rows), len(expected_rows)) + 1,
        )
        raise AssertionError(
            "Результат не совпал с независимым пересчётом "
            f"(первая отличающаяся строка данных: {first_difference}; "
            f"в файле {len(actual_rows)} строк, ожидалось {len(expected_rows)})"
        )

    total_orders = sum(values["orders"] for values in totals.values())
    total_revenue = sum(values["revenue"] for values in totals.values())
    print(
        f"OK: {len(actual_rows)} строк, orders = {total_orders}, "
        f"revenue = {total_revenue}"
    )


if __name__ == "__main__":
    main()
