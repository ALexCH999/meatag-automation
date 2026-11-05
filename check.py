#!/usr/bin/env python3
"""Recalculate daily SKU totals with pandas and compare the submitted CSV."""

from pathlib import Path

import pandas as pd


INPUT_FILE = Path("sales.csv")
RESULT_FILE = Path("daily_by_sku.csv")
EXPECTED_COLUMNS = ["sku", "order_date", "orders", "revenue"]


def fail(message: str) -> None:
    raise SystemExit(f"Ошибка проверки: {message}")


def main() -> None:
    raw = pd.read_csv(INPUT_FILE, dtype=str, keep_default_na=False)
    required = {"order_id", "order_date", "sku", "quantity", "price", "status"}
    missing = required.difference(raw.columns)
    if missing:
        fail(f"в sales.csv отсутствуют столбцы: {', '.join(sorted(missing))}")

    raw["status"] = raw["status"].str.strip().str.lower().replace({"canceled": "cancelled"})
    unique_orders = raw.drop_duplicates("order_id").copy()
    unique_order_count = unique_orders["order_id"].nunique()

    quantity = pd.to_numeric(unique_orders["quantity"], errors="coerce").fillna(0)
    price = pd.to_numeric(unique_orders["price"], errors="raise")
    unique_orders["revenue"] = (
        (quantity * price)
        .where(unique_orders["status"].eq("delivered"), 0)
        .fillna(0)
        .astype("int64")
    )

    reference = (
        unique_orders.groupby(["sku", "order_date"], as_index=False)
        .agg(orders=("order_id", "count"), revenue=("revenue", "sum"))
        .sort_values(["sku", "order_date"], kind="stable")
        .reset_index(drop=True)
    )

    try:
        actual = pd.read_csv(RESULT_FILE, dtype={"sku": str, "order_date": str}, keep_default_na=False)
    except (OSError, pd.errors.ParserError) as error:
        fail(f"не удалось прочитать {RESULT_FILE}: {error}")

    if list(actual.columns) != EXPECTED_COLUMNS:
        fail(f"неверные заголовки в {RESULT_FILE}: {list(actual.columns)!r}")

    try:
        actual["orders"] = pd.to_numeric(actual["orders"], errors="raise").astype("int64")
        actual["revenue"] = pd.to_numeric(actual["revenue"], errors="raise").astype("int64")
    except (ValueError, TypeError) as error:
        fail(f"orders и revenue должны быть целыми числами: {error}")

    actual = actual[EXPECTED_COLUMNS]
    expected = reference[EXPECTED_COLUMNS]
    if not actual.reset_index(drop=True).equals(expected.reset_index(drop=True)):
        common_rows = min(len(actual), len(expected))
        different = actual.iloc[:common_rows].ne(expected.iloc[:common_rows]).any(axis=1)
        first_difference = int(different[different].index[0]) + 1 if different.any() else common_rows + 1
        fail(
            "строки daily_by_sku.csv не совпали с пересчётом "
            f"(первая отличающаяся строка данных: {first_difference}; "
            f"в файле {len(actual)}, ожидалось {len(expected)})"
        )

    orders_total = int(actual["orders"].sum())
    revenue_total = int(actual["revenue"].sum())
    if orders_total != unique_order_count:
        fail(f"сумма orders ({orders_total}) не равна числу уникальных заказов ({unique_order_count})")
    if revenue_total != int(reference["revenue"].sum()):
        fail("общая выручка не совпала с независимым пересчётом")

    print(
        f"OK: {len(actual)} строк, уникальных заказов = {unique_order_count}, "
        f"orders = {orders_total}, revenue = {revenue_total}"
    )


if __name__ == "__main__":
    main()
