from __future__ import annotations

from datetime import datetime
from typing import Any

from app.services.analytics.common import normalize_key, parse_date


ALLOWED_QUERY_PARAMS = {
    "upload_id",
    "start_date",
    "end_date",
    "date_from",
    "date_to",
    "department",
    "company",
    "category",
    "region",
    "gender",
    "year",
    "search_keyword",
    "keyword",
    "q",
}

FIELD_ALIASES = {
    "department": ["department", "dept", "branch", "team", "course", "specialization"],
    "company": ["company", "company_name", "employer", "organization", "client", "buyer"],
    "category": ["category", "segment", "product_category", "group"],
    "region": ["region", "territory", "zone", "state", "location", "city"],
    "gender": ["gender", "sex"],
    "year": ["year", "academic_year", "graduation_year", "passout_year", "fiscal_year"],
    "date": ["date", "created_at", "updated_at", "order_date", "sale_date", "invoice_date", "attendance_date", "interview_date", "joining_date"],
}


def parse_filter_parameters(query_args: Any) -> tuple[dict[str, Any], list[str]]:
    filters: dict[str, Any] = {}
    errors: list[str] = []

    unexpected_params = sorted({key for key in query_args.keys() if key not in ALLOWED_QUERY_PARAMS})
    if unexpected_params:
        errors.extend([f"Unsupported filter parameter '{key}'." for key in unexpected_params])

    start_date_raw = _first_value(query_args, ["start_date", "date_from"])
    end_date_raw = _first_value(query_args, ["end_date", "date_to"])

    start_date = _parse_date_value(start_date_raw, "start_date", errors)
    end_date = _parse_date_value(end_date_raw, "end_date", errors)
    if start_date is not None:
        filters["start_date"] = start_date
    if end_date is not None:
        filters["end_date"] = end_date
    if start_date is not None and end_date is not None and start_date > end_date:
        errors.append("The start_date filter cannot be later than end_date.")

    for field_name in ("department", "company", "category", "region", "gender"):
        values = _parse_text_values(query_args, field_name)
        if values:
            filters[field_name] = values

        year_values, year_errors = _parse_year_values(query_args.getlist("year"))
        errors.extend(year_errors)
        if year_values:
            filters["year"] = year_values

    keyword_raw = _first_value(query_args, ["search_keyword", "keyword", "q"])
    if keyword_raw:
        filters["search_keyword"] = str(keyword_raw).strip()

    return filters, errors


def apply_filters(rows: list[dict[str, object]], filters: dict[str, Any]) -> list[dict[str, object]]:
    if not filters:
        return [dict(row) for row in rows]

    filtered_rows: list[dict[str, object]] = []
    for row in rows:
        if _row_matches_filters(row, filters):
            filtered_rows.append(dict(row))
    return filtered_rows


def _row_matches_filters(row: dict[str, object], filters: dict[str, Any]) -> bool:
    if "start_date" in filters or "end_date" in filters:
        if not _row_matches_date_range(row, filters.get("start_date"), filters.get("end_date")):
            return False

    for field_name in ("department", "company", "category", "region", "gender"):
        expected_values = filters.get(field_name)
        if expected_values and not _row_matches_alias_values(row, FIELD_ALIASES[field_name], expected_values):
            return False

    if "year" in filters and not _row_matches_year(row, filters["year"]):
        return False

    search_keyword = filters.get("search_keyword")
    if search_keyword and not _row_matches_keyword(row, search_keyword):
        return False

    return True


def _row_matches_date_range(row: dict[str, object], start_date: datetime | None, end_date: datetime | None) -> bool:
    if start_date is None and end_date is None:
        return True

    for value in _row_values_for_aliases(row, FIELD_ALIASES["date"]):
        parsed_date = parse_date(value)
        if parsed_date is None:
            continue
        if start_date is not None and parsed_date < start_date:
            continue
        if end_date is not None and parsed_date > end_date:
            continue
        return True

    return False
def _row_matches_alias_values(row: dict[str, object], aliases: list[str], expected_values: list[str]) -> bool:
    normalized_expected = {normalize_key(value) for value in expected_values if value}
    if not normalized_expected:
        return True

    for value in _row_values_for_aliases(row, aliases):
        normalized_value = normalize_key(str(value))
        if not normalized_value:
            continue
        for expected in normalized_expected:
            if normalized_value == expected or expected in normalized_value or normalized_value in expected:
                return True
    return False


def _row_matches_keyword(row: dict[str, object], keyword: str) -> bool:
    normalized_keyword = normalize_key(keyword)
    if not normalized_keyword:
        return True

    for value in row.values():
        if value in (None, ""):
            continue
        normalized_value = normalize_key(str(value))
        if normalized_keyword in normalized_value:
            return True
    return False


def _row_values_for_aliases(row: dict[str, object], aliases: list[str]) -> list[object]:
    normalized_aliases = [normalize_key(alias) for alias in aliases]
    values: list[object] = []
    for key, value in row.items():
        if value in (None, ""):
            continue
        normalized_key = normalize_key(str(key))
        if any(alias in normalized_key for alias in normalized_aliases):
            values.append(value)
    return values


def _first_value(query_args: Any, field_names: list[str]) -> str | None:
    for field_name in field_names:
        value = query_args.get(field_name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _parse_date_value(raw_value: str | None, field_name: str, errors: list[str]) -> datetime | None:
    if raw_value is None:
        return None
    parsed_value = parse_date(raw_value)
    if parsed_value is None:
        errors.append(f"Invalid {field_name} value '{raw_value}'. Use YYYY-MM-DD or a supported date format.")
    return parsed_value


def _parse_text_values(query_args: Any, field_name: str) -> list[str]:
    values = _split_values(query_args.getlist(field_name))
    return [value for value in values if value]


def _parse_year_values(raw_values: list[str]) -> tuple[list[int], list[str]]:
    years: list[int] = []
    errors: list[str] = []
    for raw_value in _split_values(raw_values):
        parsed_year = _parse_year(raw_value)
        if parsed_year is None:
            errors.append(f"Invalid year value '{raw_value}'. Use a 4-digit year.")
            continue
        if parsed_year not in years:
            years.append(parsed_year)
    return years, errors

def _parse_year(raw_value: object) -> int | None:
    if raw_value is None:
        return None
    text = str(raw_value).strip()
    if not text:
        return None
    if len(text) == 4 and text.isdigit():
        return int(text)
    if text.isdigit():
        return int(text)
    return None


def _row_matches_year(row: dict[str, object], allowed_years: list[int]) -> bool:
    if not allowed_years:
        return True

    for value in _row_values_for_aliases(row, FIELD_ALIASES["year"]):
        parsed_year = _parse_year(value)
        if parsed_year is not None and parsed_year in allowed_years:
            return True

    for value in _row_values_for_aliases(row, FIELD_ALIASES["date"]):
        parsed_date = parse_date(value)
        if parsed_date is not None and parsed_date.year in allowed_years:
            return True

    return False


def _split_values(raw_values: list[str]) -> list[str]:
    split_values: list[str] = []
    for raw_value in raw_values:
        for item in str(raw_value).split(","):
            item = item.strip()
            if item:
                split_values.append(item)
    return split_values