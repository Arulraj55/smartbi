from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from itertools import chain
import re
from typing import Iterable


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def extract_rows(rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    return [dict(row) for row in rows]


def extract_columns(rows: list[dict[str, object]]) -> list[str]:
    seen: list[str] = []
    for row in rows:
        for key in row:
            if key not in seen:
                seen.append(key)
    return seen


def find_first_value(row: dict[str, object], aliases: Iterable[str]) -> object | None:
    normalized_aliases = [normalize_key(alias) for alias in aliases]
    for key, value in row.items():
        if value in (None, ""):
            continue
        normalized_key = normalize_key(str(key))
        if any(alias in normalized_key for alias in normalized_aliases):
            return value
    return None


def find_first_column(rows: list[dict[str, object]], aliases: Iterable[str]) -> str | None:
    if not rows:
        return None
    normalized_aliases = [normalize_key(alias) for alias in aliases]
    for key in extract_columns(rows):
        normalized_key = normalize_key(key)
        if any(alias in normalized_key for alias in normalized_aliases):
            return key
    return None


def parse_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    if text.startswith("$"):
        text = text[1:]
    try:
        return float(text)
    except ValueError:
        return None


def parse_int(value: object) -> int | None:
    numeric_value = parse_float(value)
    return int(numeric_value) if numeric_value is not None else None


def parse_date(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    for parser in (
        lambda item: datetime.fromisoformat(item),
        lambda item: datetime.strptime(item, "%d/%m/%Y"),
        lambda item: datetime.strptime(item, "%m/%d/%Y"),
        lambda item: datetime.strptime(item, "%Y/%m/%d"),
        lambda item: datetime.strptime(item, "%d-%m-%Y"),
        lambda item: datetime.strptime(item, "%m-%d-%Y"),
    ):
        try:
            return parser(text)
        except ValueError:
            continue
    return None


def count_missing_values(rows: list[dict[str, object]]) -> dict[str, object]:
    per_column = Counter()
    total_missing = 0
    for row in rows:
        for key in extract_columns([row]):
            value = row.get(key)
            if value in (None, ""):
                per_column[key] += 1
                total_missing += 1
    return {"total": total_missing, "by_column": dict(per_column)}


def count_duplicate_rows(rows: list[dict[str, object]]) -> int:
    seen = set()
    duplicates = 0
    for row in rows:
        frozen = tuple(sorted((str(key), str(value)) for key, value in row.items()))
        if frozen in seen:
            duplicates += 1
        else:
            seen.add(frozen)
    return duplicates


def numeric_summary(rows: list[dict[str, object]]) -> dict[str, float | int]:
    numeric_values: list[float] = []
    for value in chain.from_iterable(row.values() for row in rows):
        parsed = parse_float(value)
        if parsed is not None:
            numeric_values.append(parsed)
    if not numeric_values:
        return {"count": 0, "sum": 0.0, "average": 0.0, "minimum": 0.0, "maximum": 0.0}
    return {
        "count": len(numeric_values),
        "sum": round(sum(numeric_values), 2),
        "average": round(sum(numeric_values) / len(numeric_values), 2),
        "minimum": round(min(numeric_values), 2),
        "maximum": round(max(numeric_values), 2),
    }


def top_frequencies(rows: list[dict[str, object]], aliases: Iterable[str], limit: int = 5) -> dict[str, object]:
    column_name = find_first_column(rows, aliases)
    if column_name is None:
        return {"labels": [], "values": [], "label": ", ".join(aliases)}
    counter = Counter(str(row.get(column_name, "Unknown")) for row in rows if row.get(column_name) not in (None, ""))
    common = counter.most_common(limit)
    return {
        "labels": [label for label, _ in common],
        "values": [count for _, count in common],
        "label": column_name,
    }


def sum_by_group(rows: list[dict[str, object]], group_aliases: Iterable[str], value_aliases: Iterable[str]) -> dict[str, object]:
    group_column = find_first_column(rows, group_aliases)
    value_column = find_first_column(rows, value_aliases)
    if group_column is None:
        return {"labels": [], "values": [], "label": ", ".join(group_aliases)}

    aggregated: defaultdict[str, float] = defaultdict(float)
    for row in rows:
        group_value = row.get(group_column)
        parsed_value = parse_float(row.get(value_column)) if value_column is not None else 1.0
        if group_value in (None, ""):
            continue
        aggregated[str(group_value)] += parsed_value if parsed_value is not None else 0.0
    ordered = sorted(aggregated.items(), key=lambda item: item[1], reverse=True)
    return {"labels": [label for label, _ in ordered], "values": [round(value, 2) for _, value in ordered], "label": group_column}


def count_by_group(rows: list[dict[str, object]], group_aliases: Iterable[str], limit: int = 10) -> dict[str, object]:
    group_column = find_first_column(rows, group_aliases)
    if group_column is None:
        return {"labels": [], "values": [], "label": ", ".join(group_aliases)}
    counter = Counter(str(row.get(group_column, "Unknown")) for row in rows if row.get(group_column) not in (None, ""))
    ordered = counter.most_common(limit)
    return {"labels": [label for label, _ in ordered], "values": [count for _, count in ordered], "label": group_column}


def monthly_counts(rows: list[dict[str, object]], date_aliases: Iterable[str], limit: int = 12) -> dict[str, object]:
    date_column = find_first_column(rows, date_aliases)
    if date_column is None:
        return {"labels": [], "values": [], "label": ", ".join(date_aliases)}
    counter: Counter[str] = Counter()
    for row in rows:
        parsed_date = parse_date(row.get(date_column))
        if parsed_date is None:
            continue
        counter[parsed_date.strftime("%Y-%m")] += 1
    ordered = sorted(counter.items())[:limit]
    return {"labels": [label for label, _ in ordered], "values": [count for _, count in ordered], "label": date_column}


def monthly_sums(rows: list[dict[str, object]], date_aliases: Iterable[str], value_aliases: Iterable[str], limit: int = 12) -> dict[str, object]:
    date_column = find_first_column(rows, date_aliases)
    value_column = find_first_column(rows, value_aliases)
    if date_column is None or value_column is None:
        return {"labels": [], "values": [], "label": f"{', '.join(date_aliases)} / {', '.join(value_aliases)}"}

    aggregated: defaultdict[str, float] = defaultdict(float)
    for row in rows:
        parsed_date = parse_date(row.get(date_column))
        parsed_value = parse_float(row.get(value_column))
        if parsed_date is None or parsed_value is None:
            continue
        aggregated[parsed_date.strftime("%Y-%m")] += parsed_value
    ordered = sorted(aggregated.items())[:limit]
    return {"labels": [label for label, _ in ordered], "values": [round(value, 2) for _, value in ordered], "label": value_column}


def ratio(positive: int, total: int) -> float:
    return round((positive / total) * 100, 2) if total else 0.0