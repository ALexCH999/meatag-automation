#!/usr/bin/env python3
"""
Задача 1: Обработка выгрузки заказов интернет-магазина и суточная агрегация по SKU.

Что делает скрипт:
1. Читает исходный файл sales.csv.
2. Проверяет уникальность заказов по order_id: каждый заказ учитывается ровно один раз.
3. Очищает и нормализует статусы заказов (убирает пробелы, приводит к нижнему регистру,
   исправляет опечатку 'canceled' -> 'cancelled').
4. Группирует данные по паре (sku, order_date):
   - orders: количество уникальных заказов за день (включая отменённые).
   - revenue: сумма (quantity * price) только для выкупленных заказов (status == 'delivered').
5. Сортирует результат сначала по sku (по алфавиту), затем по order_date (по возрастанию даты).
6. Записывает результат в файл daily_by_sku.csv с колонками: sku, order_date, orders, revenue.
"""

import csv
from collections import defaultdict
from pathlib import Path


def clean_status(raw_status: str) -> str:
    """
    Очистка и нормализация статуса заказа:
    - убираем случайные пробелы по краям (например, 'delivered ');
    - приводим к нижнему регистру ('Delivered', 'DELIVERED' -> 'delivered');
    - исправляем опечатку с одной 'l': 'canceled' -> 'cancelled'.
    """
    if not raw_status:
        return ""
    status = raw_status.strip().lower()
    if status == "canceled":
        return "cancelled"
    return status


def main() -> None:
    # Пути к файлам
    input_file = Path("sales.csv")
    output_file = Path("daily_by_sku.csv")

    if not input_file.exists():
        print(f"Ошибка: входной файл '{input_file}' не найден в текущей папке.")
        return

    # Множество для отслеживания уже обработанных order_id (устранение дублей)
    seen_orders = set()

    # Словарь для агрегации: ключ — кортеж (sku, order_date)
    # Значение — словарь с количеством заказов и суммой выручки
    # defaultdict автоматически создаёт {"orders": 0, "revenue": 0} для новой пары (sku, date)
    daily_stats = defaultdict(lambda: {"orders": 0, "revenue": 0})

    # Счётчики для проверки и итогового отчёта
    total_rows = 0
    duplicates_count = 0
    delivered_count = 0
    cancelled_count = 0

    print("Читаем и обрабатываем sales.csv...")

    # Используем utf-8-sig на случай наличия BOM в файле
    with open(input_file, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            total_rows += 1
            order_id = row["order_id"].strip()

            # Условие ТЗ: один заказ учитывается один раз, даже если встретился дважды
            if order_id in seen_orders:
                duplicates_count += 1
                continue
            seen_orders.add(order_id)

            sku = row["sku"].strip()
            order_date = row["order_date"].strip()
            status = clean_status(row["status"])

            key = (sku, order_date)

            # 1. orders — считаем все заказы по артикулу за день (включая отменённые)
            daily_stats[key]["orders"] += 1

            # 2. revenue — считаем выручку (quantity * price) только по выкупленным (delivered)
            if status == "delivered":
                delivered_count += 1
                quantity = int(row["quantity"])
                price = int(row["price"])
                daily_stats[key]["revenue"] += quantity * price
            elif status == "cancelled":
                cancelled_count += 1

    # Условие ТЗ: строки отсортированы по sku, затем по дате
    # Сортировка кортежей (sku, order_date) в Python автоматически сортирует
    # сначала по первому элементу (sku), затем по второму (order_date).
    sorted_keys = sorted(daily_stats.keys())

    print(f"Записываем результат в {output_file}...")

    # Запись итогового CSV-файла
    with open(output_file, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        # Заголовки строго по ТЗ
        writer.writerow(["sku", "order_date", "orders", "revenue"])

        for sku, order_date in sorted_keys:
            stats = daily_stats[(sku, order_date)]
            writer.writerow([sku, order_date, stats["orders"], stats["revenue"]])

    # Вывод контрольных показателей для самопроверки
    total_unique_orders = len(seen_orders)
    total_revenue = sum(item["revenue"] for item in daily_stats.values())
    total_orders_check = sum(item["orders"] for item in daily_stats.values())

    print("\n" + "=" * 50)
    print("ИТОГИ ВЫПОЛНЕНИЯ ЗАДАНИЯ 1:")
    print(f"  Всего строк в исходном файле:     {total_rows}")
    print(f"  Пропущено дубликатов строк:       {duplicates_count}")
    print(f"  Уникальных заказов учтено:        {total_unique_orders}")
    print(f"    - Доставлено (delivered):       {delivered_count}")
    print(f"    - Отменено (cancelled):         {cancelled_count}")
    print(f"  Общая выручка (revenue):          {total_revenue:,} руб.")
    print(f"  Сформировано строк в {output_file}: {len(sorted_keys)}")
    print(f"  Контрольная сумма заказов:        {total_orders_check} (совпадает: {total_orders_check == total_unique_orders})")
    print("=" * 50)


if __name__ == "__main__":
    main()
