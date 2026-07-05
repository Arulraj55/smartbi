from __future__ import annotations

from app.services.analytics.common import count_by_group, find_first_value, parse_float


def analyze(rows: list[dict[str, object]]) -> dict[str, object]:
    total_products = len(rows)
    low_stock_items = 0
    out_of_stock = 0
    stock_value = 0.0

    for row in rows:
        quantity = parse_float(find_first_value(row, ["stock_qty", "quantity", "qty", "stock", "on_hand", "available_stock"])) or 0.0
        reorder = parse_float(find_first_value(row, ["reorder_level", "reorder", "minimum_stock", "min_stock"])) or 0.0
        unit_price = parse_float(find_first_value(row, ["unit_price", "price", "cost", "rate"])) or 0.0
        if quantity <= reorder:
            low_stock_items += 1
        if quantity <= 0:
            out_of_stock += 1
        stock_value += quantity * unit_price

    return {
        "domain": "Inventory",
        "kpis": {
            "total_products": total_products,
            "low_stock_items": low_stock_items,
            "out_of_stock": out_of_stock,
            "stock_value": round(stock_value, 2),
            "category_distribution": count_by_group(rows, ["category", "product_category", "type"]),
            "supplier_distribution": count_by_group(rows, ["supplier", "vendor", "provider"]),
        },
        "charts": {
            "primary": count_by_group(rows, ["category", "product_category", "type"]),
            "secondary": count_by_group(rows, ["supplier", "vendor", "provider"]),
        },
        "insights": [f"{low_stock_items} items are at or below reorder level.", f"Stock value is {round(stock_value, 2)}."],
    }