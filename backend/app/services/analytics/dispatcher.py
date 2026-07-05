from __future__ import annotations

from collections.abc import Iterable

from app.services.analytics.attendance import analyze as analyze_attendance
from app.services.analytics.generic import analyze as analyze_generic
from app.services.analytics.hr import analyze as analyze_hr
from app.services.analytics.inventory import analyze as analyze_inventory
from app.services.analytics.placement import analyze as analyze_placement
from app.services.analytics.sales import analyze as analyze_sales
from app.services.domain_service import detect_domain


ANALYZER_MAP = {
    "Placement Management": analyze_placement,
    "HR Management": analyze_hr,
    "Retail Sales": analyze_sales,
    "Inventory": analyze_inventory,
    "Student Attendance": analyze_attendance,
    "Generic": analyze_generic,
}


def detect_domain_from_columns(
    column_names: Iterable[str],
    sample_records: list[dict[str, object]] | None = None,
) -> tuple[str, float]:
    return detect_domain(list(column_names), sample_records=sample_records)


def detect_domain_from_records(records: list[dict[str, object]]) -> tuple[str, float]:
    if not records:
        return "Generic", 0.0
    return detect_domain_from_columns(records[0].keys(), sample_records=records)


def build_analytics_payload(records: list[dict[str, object]]) -> dict[str, object]:
    domain_name, confidence = detect_domain_from_records(records)
    analyzer = ANALYZER_MAP.get(domain_name, analyze_generic)
    analysis = analyzer(records)

    charts = _extract_charts(domain_name, analysis, records)
    
    # Fallback to Generic if the specific domain analyzer couldn't generate any charts
    if domain_name != "Generic":
        has_charts = any(bool(chart.get("values")) for chart in charts.values() if isinstance(chart, dict))
        if not has_charts:
            domain_name = "Generic"
            analysis = analyze_generic(records)
            charts = _extract_charts(domain_name, analysis, records)

    return {
        "domain": {"name": domain_name, "confidence": confidence},
        "detected_domain": domain_name,
        "confidence": confidence,
        "analytics": analysis,
        "kpis": _extract_kpis(domain_name, analysis, records),
        "charts": charts,
        "insights": _extract_insights(analysis),
    }


# ── KPI extraction ────────────────────────────────────────────────────────────

def _extract_kpis(
    domain_name: str,
    analysis: dict[str, object],
    records: list[dict[str, object]],
) -> dict[str, object]:
    kpis = analysis.get("kpis", {}) if isinstance(analysis.get("kpis", {}), dict) else {}

    if domain_name == "Placement Management":
        return {
            "total_students": kpis.get("total_students", 0),
            "placed_students": kpis.get("placed_students", 0),
            "unplaced_students": kpis.get("unplaced_students", 0),
            "placement_%": kpis.get("placement_percentage", 0.0),
            "placement_percentage": kpis.get("placement_percentage", 0.0),
            "avg_package": kpis.get("average_package", 0.0),
            "highest_package": kpis.get("highest_package", 0.0),
        }
    if domain_name == "HR Management":
        return {
            "total_employees": kpis.get("total_employees", 0),
            "departments": kpis.get("department_count", 0),
            "avg_salary": kpis.get("average_salary", 0.0),
            "attendance_%": kpis.get("attendance_percentage", 0.0),
            "attrition_count": kpis.get("attrition_count", 0),
        }
    if domain_name == "Retail Sales":
        return {
            "total_revenue": kpis.get("total_revenue", 0.0),
            "total_orders": kpis.get("total_orders", 0),
            "avg_order_value": kpis.get("average_order_value", 0.0),
        }
    if domain_name == "Inventory":
        return {
            "total_products": kpis.get("total_products", 0),
            "low_stock_items": kpis.get("low_stock_items", 0),
            "out_of_stock": kpis.get("out_of_stock", 0),
            "stock_value": kpis.get("stock_value", 0.0),
        }
    if domain_name == "Student Attendance":
        return {
            "attendance_%": kpis.get("attendance_percentage", 0.0),
            "absent_%": kpis.get("absent_percentage", 0.0),
        }
    # Generic — only scalar KPIs
    return {
        "row_count": kpis.get("row_count", len(records)),
        "column_count": kpis.get("column_count", 0),
        "duplicate_rows": kpis.get("duplicate_rows", 0),
    }


# ── Chart extraction ──────────────────────────────────────────────────────────

def _safe_chart(raw: object, fallback_label: str = "") -> dict[str, object]:
    if isinstance(raw, dict) and raw.get("labels") is not None:
        out = dict(raw)
        if "chart_type" not in out:
            out["chart_type"] = "bar"
        return out
    return {"labels": [], "values": [], "label": fallback_label, "chart_type": "bar"}


def _extract_charts(
    domain_name: str,
    analysis: dict[str, object],
    records: list[dict[str, object]],
) -> dict[str, object]:
    charts = analysis.get("charts", {}) if isinstance(analysis.get("charts", {}), dict) else {}

    if domain_name == "Placement Management":
        return {
            "primary": _safe_chart(charts.get("company_wise_placements"), "Company-wise Placements"),
            "secondary": _safe_chart(charts.get("department_wise_placements"), "Dept-wise Placements"),
            "tertiary": _safe_chart(charts.get("gender_wise_placements"), "Gender-wise Placements"),
            "quaternary": _safe_chart(charts.get("year_wise_placements"), "Year-wise Placements"),
        }
    if domain_name == "HR Management":
        return {
            "primary": _safe_chart(charts.get("primary"), "Department Distribution"),
            "secondary": _safe_chart(charts.get("secondary"), "Gender Distribution"),
            "tertiary": _safe_chart(
                analysis.get("kpis", {}).get("experience_distribution"),  # type: ignore[union-attr]
                "Experience Distribution",
            ),
            "quaternary": {"labels": [], "values": [], "label": "", "chart_type": "bar"},
        }
    if domain_name == "Retail Sales":
        return {
            "primary": _safe_chart(charts.get("primary"), "Monthly Sales"),
            "secondary": _safe_chart(charts.get("secondary"), "Region-wise Sales"),
            "tertiary": _safe_chart(
                analysis.get("kpis", {}).get("top_products"),  # type: ignore[union-attr]
                "Top Products",
            ),
            "quaternary": _safe_chart(
                analysis.get("kpis", {}).get("top_categories"),  # type: ignore[union-attr]
                "Top Categories",
            ),
        }
    if domain_name == "Inventory":
        return {
            "primary": _safe_chart(charts.get("primary"), "Category Distribution"),
            "secondary": _safe_chart(charts.get("secondary"), "Supplier Distribution"),
            "tertiary": {"labels": [], "values": [], "label": "", "chart_type": "bar"},
            "quaternary": {"labels": [], "values": [], "label": "", "chart_type": "bar"},
        }
    if domain_name == "Student Attendance":
        return {
            "primary": _safe_chart(charts.get("primary"), "Monthly Attendance"),
            "secondary": _safe_chart(charts.get("secondary"), "Class-wise Attendance"),
            "tertiary": _safe_chart(
                analysis.get("kpis", {}).get("subject_wise_attendance"),  # type: ignore[union-attr]
                "Subject-wise Attendance",
            ),
            "quaternary": {"labels": [], "values": [], "label": "", "chart_type": "bar"},
        }
    # Generic — pass through all charts generated by generic.py
    return {
        "primary": _safe_chart(charts.get("primary"), "Trend"),
        "secondary": _safe_chart(charts.get("secondary"), "Distribution"),
        "tertiary": _safe_chart(charts.get("tertiary"), "Categorical"),
        "quaternary": _safe_chart(charts.get("quaternary"), "Completeness"),
    }


# ── Insights ──────────────────────────────────────────────────────────────────

def _extract_insights(analysis: dict[str, object]) -> list[str]:
    insights = analysis.get("insights")
    if isinstance(insights, list):
        return [str(item) for item in insights]
    if isinstance(insights, str):
        return [insights]
    return []