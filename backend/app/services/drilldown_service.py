from __future__ import annotations

from typing import Any

from app.services.analytics.common import find_first_value, normalize_key, parse_float


DIMENSION_ALIASES = {
    "company": ["company", "company_name", "employer", "organization", "client", "buyer"],
    "department": ["department", "dept", "branch", "team", "course", "specialization"],
    "category": ["category", "segment", "product_category", "group", "type"],
    "region": ["region", "territory", "zone", "state", "location", "city"],
    "gender": ["gender", "sex"],
    "year": ["year", "academic_year", "graduation_year", "passout_year", "fiscal_year"],
    "class": ["class", "section", "batch", "grade"],
    "subject": ["subject", "course", "paper"],
    "status": ["status", "placement_status", "offer_status", "attendance", "presence", "present_absent"],
    "supplier": ["supplier", "vendor", "provider"],
    "product": ["product", "product_name", "item", "sku"],
    "customer": ["customer", "customer_name", "client", "buyer"],
}

METRIC_ALIASES = {
    "low_stock": {"low_stock", "low_stock_items", "low stock"},
    "out_of_stock": {"out_of_stock", "out of stock", "outofstock"},
    "placed": {"placed", "placed_students", "placement"},
    "unplaced": {"unplaced", "unplaced_students", "not_placed"},
    "present": {"present", "attendance_present"},
    "absent": {"absent", "attendance_absent"},
}

PLACED_STATUS_WORDS = {"placed", "selected", "hired", "joined", "offer accepted", "converted"}
PRESENT_STATUS_WORDS = {"present", "p", "yes", "1", "available", "active"}
ABSENT_STATUS_WORDS = {"absent", "a", "no", "0", "leave"}


def parse_drilldown_parameters(query_args: Any) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    field = _first_value(query_args, ["field", "dimension", "column", "group"])
    value = _first_value(query_args, ["value", "label", "key", "name"])
    metric = _first_value(query_args, ["metric", "kpi"])
    limit = _parse_int(_first_value(query_args, ["limit"]), "limit", errors, default=100)
    offset = _parse_int(_first_value(query_args, ["offset"]), "offset", errors, default=0)

    if limit is not None and (limit < 1 or limit > 500):
        errors.append("limit must be between 1 and 500.")
    if offset is not None and offset < 0:
        errors.append("offset cannot be negative.")
    if not metric and not field:
        errors.append("Provide either a metric or a field/dimension to drill into.")
    if field and value is None:
        errors.append("Provide a value/label when drilling into a field or dimension.")

    parameters = {
        "field": field,
        "value": value,
        "metric": metric,
        "limit": limit if limit is not None else 100,
        "offset": offset if offset is not None else 0,
    }
    return parameters, errors


def build_drilldown_result(rows: list[dict[str, object]], parameters: dict[str, Any]) -> tuple[list[dict[str, object]], dict[str, object]]:
    metric = parameters.get("metric")
    field = parameters.get("field")
    value = parameters.get("value")
    limit = int(parameters.get("limit", 100))
    offset = int(parameters.get("offset", 0))

    if metric:
        matched_rows = _filter_by_metric(rows, str(metric))
        drilldown_type = "metric"
        normalized_target = _canonical_metric(metric)
    else:
        matched_rows = _filter_by_dimension(rows, str(field), value)
        drilldown_type = "dimension"
        normalized_target = normalize_key(str(field))

    paged_rows = [dict(row) for row in matched_rows[offset : offset + limit]]
    metadata = {
        "type": drilldown_type,
        "target": normalized_target,
        "field": field,
        "value": value,
        "metric": metric,
        "total_row_count": len(rows),
        "matched_row_count": len(matched_rows),
        "returned_row_count": len(paged_rows),
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < len(matched_rows),
    }
    return paged_rows, metadata


def extract_columns(rows: list[dict[str, object]]) -> list[str]:
    columns: list[str] = []
    for row in rows:
        for column in row:
            if column not in columns:
                columns.append(column)
    return columns


def _filter_by_dimension(rows: list[dict[str, object]], field: str, expected_value: object) -> list[dict[str, object]]:
    normalized_field = normalize_key(field)
    aliases = DIMENSION_ALIASES.get(normalized_field, [field])
    return [dict(row) for row in rows if _row_matches_dimension(row, aliases, expected_value)]


def _filter_by_metric(rows: list[dict[str, object]], metric: str) -> list[dict[str, object]]:
    canonical_metric = _canonical_metric(metric)
    if canonical_metric == "low_stock":
        return [dict(row) for row in rows if _is_low_stock(row)]
    if canonical_metric == "out_of_stock":
        return [dict(row) for row in rows if _stock_quantity(row) <= 0]
    if canonical_metric == "placed":
        return [dict(row) for row in rows if _is_placed(row)]
    if canonical_metric == "unplaced":
        return [dict(row) for row in rows if not _is_placed(row)]
    if canonical_metric == "present":
        return [dict(row) for row in rows if _attendance_status(row) in PRESENT_STATUS_WORDS]
    if canonical_metric == "absent":
        return [dict(row) for row in rows if _attendance_status(row) in ABSENT_STATUS_WORDS]
    return []


def _row_matches_dimension(row: dict[str, object], aliases: list[str], expected_value: object) -> bool:
    normalized_expected = normalize_key(str(expected_value))
    if not normalized_expected:
        return True

    normalized_aliases = [normalize_key(alias) for alias in aliases]
    for key, value in row.items():
        if value in (None, ""):
            continue
        normalized_key = normalize_key(str(key))
        if not any(alias in normalized_key or normalized_key in alias for alias in normalized_aliases):
            continue
        normalized_value = normalize_key(str(value))
        if normalized_value == normalized_expected:
            return True
    return False


def _canonical_metric(metric: object) -> str:
    normalized_metric = normalize_key(str(metric))
    for canonical, aliases in METRIC_ALIASES.items():
        normalized_aliases = {normalize_key(alias) for alias in aliases}
        if normalized_metric in normalized_aliases:
            return canonical
    return normalized_metric


def _is_low_stock(row: dict[str, object]) -> bool:
    quantity = _stock_quantity(row)
    reorder = parse_float(find_first_value(row, ["reorder_level", "reorder", "minimum_stock", "min_stock"])) or 0.0
    return quantity <= reorder


def _stock_quantity(row: dict[str, object]) -> float:
    return parse_float(find_first_value(row, ["stock_qty", "quantity", "qty", "stock", "on_hand", "available_stock"])) or 0.0


def _is_placed(row: dict[str, object]) -> bool:
    status_value = str(find_first_value(row, ["status", "placement_status", "offer_status", "result"]) or "").strip().lower()
    return status_value in PLACED_STATUS_WORDS or find_first_value(row, ["package", "ctc", "offer_ctc"]) is not None


def _attendance_status(row: dict[str, object]) -> str:
    return str(find_first_value(row, ["attendance", "status", "presence", "present_absent", "attendance_status"]) or "").strip().lower()


def _first_value(query_args: Any, field_names: list[str]) -> str | None:
    for field_name in field_names:
        value = query_args.get(field_name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _parse_int(raw_value: str | None, field_name: str, errors: list[str], *, default: int) -> int | None:
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        errors.append(f"{field_name} must be an integer.")
        return None
