from __future__ import annotations

from collections import Counter, defaultdict

from app.services.analytics.common import count_by_group, find_first_value, monthly_sums, parse_float, ratio


def analyze(rows: list[dict[str, object]]) -> dict[str, object]:
    total_orders = len(rows)
    revenue_values = [parse_float(find_first_value(row, ["amount", "revenue", "sales", "total", "value"])) for row in rows]
    revenue_values = [value for value in revenue_values if value is not None]
    total_revenue = round(sum(revenue_values), 2)
    average_order_value = round(total_revenue / total_orders, 2) if total_orders else 0.0

    top_products = count_by_group(rows, ["product", "product_name", "item", "sku"])
    top_categories = count_by_group(rows, ["category", "segment", "product_category"])
    top_customers = count_by_group(rows, ["customer", "customer_name", "client", "buyer"])
    region_wise_sales = monthly_sales_group(rows, ["region", "territory", "zone"], ["amount", "revenue", "sales", "total", "value"])
    monthly_sales = monthly_sums(rows, ["order_date", "sale_date", "invoice_date", "date"], ["amount", "revenue", "sales", "total", "value"])

    sales_trend = monthly_sales

    return {
        "domain": "Retail Sales",
        "kpis": {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "average_order_value": average_order_value,
            "monthly_sales": monthly_sales,
            "top_products": top_products,
            "top_categories": top_categories,
            "top_customers": top_customers,
            "sales_trend": sales_trend,
            "region_wise_sales": region_wise_sales,
        },
        "charts": {
            "primary": monthly_sales,
            "secondary": region_wise_sales,
        },
        "insights": [f"Total revenue is {total_revenue}.", f"Average order value is {average_order_value}."] ,
    }


def monthly_sales_group(rows: list[dict[str, object]], group_aliases: list[str], value_aliases: list[str]) -> dict[str, object]:
    from app.services.analytics.common import count_by_group, find_first_column, parse_float

    group_column = find_first_column(rows, group_aliases)
    value_column = find_first_column(rows, value_aliases)
    if group_column is None:
        return {"labels": [], "values": [], "label": ", ".join(group_aliases)}
    aggregated: defaultdict[str, float] = defaultdict(float)
    for row in rows:
        group_value = row.get(group_column)
        parsed_value = parse_float(row.get(value_column)) if value_column is not None else None
        if group_value in (None, ""):
            continue
        aggregated[str(group_value)] += parsed_value or 0.0
    ordered = sorted(aggregated.items(), key=lambda item: item[1], reverse=True)
    return {"labels": [label for label, _ in ordered], "values": [round(value, 2) for _, value in ordered], "label": group_column}