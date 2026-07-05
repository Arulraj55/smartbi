from __future__ import annotations

import math
from collections import Counter
from datetime import datetime
from typing import Iterable


def _safe_parse_date(value: object) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def calculate_summary_metrics(rows: Iterable[dict[str, object]]) -> dict[str, object]:
    row_list = list(rows)
    total_rows = len(row_list)
    numeric_values = []
    domain_counter = Counter(str(row.get("detected_domain", "Unknown")) for row in row_list)
    for row in row_list:
        for value in row.values():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                fval = float(value)
                if not (math.isnan(fval) or math.isinf(fval)):
                    numeric_values.append(fval)

    average_value = round(sum(numeric_values) / len(numeric_values), 2) if numeric_values else 0.0
    return {
        "total_rows": total_rows,
        "average_numeric_value": average_value,
        "domain_breakdown": dict(domain_counter),
    }


def calculate_rankings(rows: Iterable[dict[str, object]], value_field: str, top_n: int = 5) -> list[dict[str, object]]:
    ranked_rows = sorted(
        [row for row in rows if row.get(value_field) is not None],
        key=lambda row: float(row.get(value_field, 0)),
        reverse=True,
    )
    return ranked_rows[:top_n]


def calculate_percentages(rows: Iterable[dict[str, object]], field_name: str) -> dict[str, float]:
    row_list = list(rows)
    total_rows = len(row_list) or 1
    counter = Counter(str(row.get(field_name, "Unknown")) for row in row_list)
    return {key: round((count / total_rows) * 100, 2) for key, count in counter.items()}


def calculate_trends(rows: Iterable[dict[str, object]], date_field: str, value_field: str) -> list[dict[str, object]]:
    monthly_totals: dict[str, float] = {}
    for row in rows:
        date_value = row.get(date_field)
        numeric_value = row.get(value_field)
        if date_value is None or numeric_value is None:
            continue
        parsed_date = _safe_parse_date(date_value)
        if parsed_date is None:
            continue
        bucket = parsed_date.strftime("%Y-%m")
        monthly_totals[bucket] = monthly_totals.get(bucket, 0.0) + float(numeric_value)
    return [{"month": month, "value": round(total, 2)} for month, total in sorted(monthly_totals.items())]


def monthly_summary(date_values: Iterable[str]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for value in date_values:
        parsed = _safe_parse_date(value)
        if parsed is None:
            continue
        bucket = parsed.strftime("%Y-%m")
        summary[bucket] = summary.get(bucket, 0) + 1
    return summary