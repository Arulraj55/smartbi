from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.analytics.engine import analyze_dataset
from app.services.database_service import DatabaseService


@dataclass(slots=True)
class ComparisonError(Exception):
    message: str
    status_code: int = 400
    errors: list[str] | None = None


def parse_comparison_parameters(query_args: Any) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    upload_a = _parse_required_int(query_args.get("upload_a"), "upload_a", errors)
    upload_b = _parse_required_int(query_args.get("upload_b"), "upload_b", errors)
    include_charts = _parse_bool(query_args.get("chart"), default=False)
    summary_only = _parse_bool(query_args.get("summary_only"), default=False)

    return {
        "upload_a": upload_a,
        "upload_b": upload_b,
        "chart": include_charts,
        "summary_only": summary_only,
    }, errors


def compare_uploads(database_service: DatabaseService, upload_a_id: int, upload_b_id: int, *, include_charts: bool = False, summary_only: bool = False) -> dict[str, Any]:
    upload_a, rows_a = database_service.fetch_upload_dataset(upload_a_id)
    upload_b, rows_b = database_service.fetch_upload_dataset(upload_b_id)

    if upload_a is None or upload_b is None:
        missing = []
        if upload_a is None:
            missing.append("upload_a")
        if upload_b is None:
            missing.append("upload_b")
        raise ComparisonError("One or more uploads do not exist.", 404, missing)
    if not rows_a or not rows_b:
        empty = []
        if not rows_a:
            empty.append("upload_a")
        if not rows_b:
            empty.append("upload_b")
        raise ComparisonError("One or more uploads are empty.", 400, empty)

    analysis_a = analyze_dataset(rows_a)
    analysis_b = analyze_dataset(rows_b)
    domain_a = str(analysis_a["domain"]["name"])
    domain_b = str(analysis_b["domain"]["name"])
    if domain_a != domain_b:
        raise ComparisonError("Uploads must have matching domains.", 400, [f"upload_a={domain_a}", f"upload_b={domain_b}"])

    old_metrics = _extract_comparable_metrics(analysis_a)
    new_metrics = _extract_comparable_metrics(analysis_b)
    comparison = _compare_metric_sets(old_metrics, new_metrics)
    response: dict[str, Any] = {
        "domain": domain_a,
        "upload_a": upload_a,
        "upload_b": upload_b,
        "comparison": comparison,
        "charts": _build_chart_payload(comparison) if include_charts and not summary_only else {},
    }

    if not summary_only:
        response["analytics"] = {
            "upload_a": {
                "row_count": analysis_a["row_count"],
                "column_count": analysis_a["column_count"],
                "kpis": analysis_a["kpis"],
                "charts": analysis_a["charts"],
            },
            "upload_b": {
                "row_count": analysis_b["row_count"],
                "column_count": analysis_b["column_count"],
                "kpis": analysis_b["kpis"],
                "charts": analysis_b["charts"],
            },
        }
    return response


def calculate_metric_change(old_value: float, new_value: float) -> dict[str, float | str]:
    difference = round(new_value - old_value, 2)
    if old_value == 0:
        growth_percent = 0.0 if new_value == 0 else 100.0
    else:
        growth_percent = round((difference / abs(old_value)) * 100, 2)

    if difference > 0:
        trend = "Increase"
    elif difference < 0:
        trend = "Decrease"
    else:
        trend = "No Change"

    return {
        "old": round(old_value, 2),
        "new": round(new_value, 2),
        "difference": difference,
        "growth_percent": growth_percent,
        "trend": trend,
    }


def _extract_comparable_metrics(analysis: dict[str, Any]) -> dict[str, float]:
    metrics = {
        "rows": float(analysis.get("row_count", 0)),
        "columns": float(analysis.get("column_count", 0)),
    }
    metrics.update(_flatten_numeric_metrics(analysis.get("kpis", {})))
    return metrics


def _flatten_numeric_metrics(payload: Any, prefix: str = "") -> dict[str, float]:
    metrics: dict[str, float] = {}
    if isinstance(payload, dict):
        if _is_chart_payload(payload):
            values = [_to_float(value) for value in payload.get("values", [])]
            numeric_values = [value for value in values if value is not None]
            if prefix:
                metrics[f"{prefix}_total"] = round(sum(numeric_values), 2)
                metrics[f"{prefix}_groups"] = float(len(payload.get("labels", [])))
            return metrics

        for key, value in payload.items():
            metric_key = f"{prefix}_{key}" if prefix else str(key)
            metrics.update(_flatten_numeric_metrics(value, metric_key))
        return metrics

    if isinstance(payload, list):
        numeric_values = [_to_float(item) for item in payload]
        numeric_values = [value for value in numeric_values if value is not None]
        if numeric_values and prefix:
            metrics[f"{prefix}_total"] = round(sum(numeric_values), 2)
            metrics[f"{prefix}_count"] = float(len(numeric_values))
        return metrics

    numeric_value = _to_float(payload)
    if numeric_value is not None and prefix:
        metrics[prefix] = numeric_value
    return metrics


def _compare_metric_sets(old_metrics: dict[str, float], new_metrics: dict[str, float]) -> dict[str, dict[str, float | str]]:
    comparison: dict[str, dict[str, float | str]] = {}
    for key in sorted(set(old_metrics) | set(new_metrics)):
        comparison[key] = calculate_metric_change(old_metrics.get(key, 0.0), new_metrics.get(key, 0.0))
    return comparison


def _build_chart_payload(comparison: dict[str, dict[str, float | str]]) -> dict[str, Any]:
    labels = list(comparison.keys())
    old_values = [comparison[label]["old"] for label in labels]
    new_values = [comparison[label]["new"] for label in labels]
    growth_values = [comparison[label]["growth_percent"] for label in labels]

    return {
        "bar_chart": {
            "labels": labels,
            "datasets": [
                {"label": "Upload A", "data": old_values},
                {"label": "Upload B", "data": new_values},
            ],
        },
        "line_chart": {
            "labels": ["Upload A", "Upload B"],
            "datasets": [
                {"label": label, "data": [comparison[label]["old"], comparison[label]["new"]]}
                for label in labels[:12]
            ],
        },
        "comparison_chart": {
            "labels": labels,
            "old_values": old_values,
            "new_values": new_values,
        },
        "trend_chart": {
            "labels": labels,
            "values": growth_values,
            "label": "Growth %",
        },
    }


def _is_chart_payload(payload: dict[str, Any]) -> bool:
    return isinstance(payload.get("labels"), list) and isinstance(payload.get("values"), list)


def _parse_required_int(raw_value: object, field_name: str, errors: list[str]) -> int | None:
    if raw_value is None or str(raw_value).strip() == "":
        errors.append(f"{field_name} is required.")
        return None
    try:
        return int(str(raw_value))
    except ValueError:
        errors.append(f"{field_name} must be an integer.")
        return None


def _parse_bool(raw_value: object, *, default: bool) -> bool:
    if raw_value is None:
        return default
    return str(raw_value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _to_float(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None
