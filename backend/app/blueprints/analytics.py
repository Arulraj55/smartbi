from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.services.auth_service import login_required
from app.services.comparison_service import ComparisonError, compare_uploads, parse_comparison_parameters
from app.services.database_service import DatabaseService
from app.services.drilldown_service import build_drilldown_result, extract_columns, parse_drilldown_parameters
from app.services.filter_service import apply_filters, parse_filter_parameters
from app.services.analytics.engine import analyze_dataset
from app.services.analytics_service import calculate_percentages, calculate_rankings, calculate_summary_metrics, calculate_trends
from app.services.openrouter_service import detect_domain_ai

analytics_bp = Blueprint("analytics", __name__)


def get_analytics_context() -> tuple[dict[str, object], list[dict[str, object]]]:
    database_service = DatabaseService(current_app.config["DATABASE_URL"])
    upload_id = request.args.get("upload_id", type=int)
    upload, rows = database_service.fetch_upload_dataset(upload_id)
    if upload is None:
        return {}, []
    return upload, rows


def build_analytics_response() -> tuple[dict[str, object] | None, int]:
    upload, rows = get_analytics_context()
    if not upload:
        return None, 404
    return build_analytics_response_from_dataset(upload, rows), 200


def build_analytics_response_from_dataset(
    upload: dict[str, object],
    rows: list[dict[str, object]],
    *,
    applied_filters: dict[str, object] | None = None,
) -> dict[str, object]:
    analysis = analyze_dataset(rows)
    response: dict[str, object] = {
        "upload": upload,
        "domain": analysis["domain"],
        "row_count": analysis["row_count"],
        "column_count": analysis["column_count"],
        "kpis": analysis["kpis"],
        "charts": analysis["charts"],
        "insights": analysis["insights"],
    }
    if applied_filters is not None:
        response["filters"] = applied_filters
        response["total_row_count"] = int(upload.get("row_count", len(rows)))
        response["filtered_row_count"] = analysis["row_count"]
    return response


# ── GET endpoints ─────────────────────────────────────────────────────────────

@analytics_bp.get("/")
@login_required
def analytics_index() -> tuple[dict[str, object], int]:
    return jsonify({"message": "Analytics endpoint"}), 200


@analytics_bp.get("/summary")
@login_required
def analytics_summary_get() -> tuple[dict[str, object], int]:
    response, status_code = build_analytics_response()
    if status_code != 200 or response is None:
        return jsonify({"message": "No analytics data available."}), status_code
    return jsonify(response), status_code


@analytics_bp.get("/latest")
@login_required
def latest_analytics() -> tuple[dict[str, object], int]:
    database_service = DatabaseService(current_app.config["DATABASE_URL"])
    row = database_service.fetch_latest_upload()
    return jsonify({"item": row}), 200


@analytics_bp.get("/dashboard")
@login_required
def analytics_dashboard() -> tuple[dict[str, object], int]:
    upload_id = request.args.get("upload_id", type=int)
    database_service = DatabaseService(current_app.config["DATABASE_URL"])

    # Fetch upload metadata only (no row fetch needed if summary is stored)
    upload = (
        database_service.fetch_upload_by_id(upload_id)
        if upload_id
        else database_service.fetch_latest_upload()
    )
    if upload is None:
        return jsonify({"message": "No analytics data available."}), 404

    # ── Fast path: use stored analytics from summary_json ─────────────────
    stored_summary = upload.get("summary_json") or {}
    analytics_engine = stored_summary.get("analytics_engine") if isinstance(stored_summary, dict) else None
    ai_result = stored_summary.get("ai_result") if isinstance(stored_summary, dict) else None

    if (
        analytics_engine
        and isinstance(analytics_engine, dict)
        and analytics_engine.get("kpis")
        and analytics_engine.get("charts")
    ):
        analytics_payload = analytics_engine
    else:
        # Fallback: fetch rows and re-run analysis (older uploads without stored analytics)
        _, rows = database_service.fetch_upload_dataset(int(upload["id"]))
        analytics_payload = analyze_dataset(rows)

    # ── Prefer AI-computed charts when available ───────────────────────────
    # AI charts are richer (use actual column data) vs rule-based fallbacks.
    # Convert computed_charts list → {primary, secondary, tertiary, quaternary} dict.
    if (
        isinstance(ai_result, dict)
        and ai_result.get("ai_powered")
        and ai_result.get("computed_charts")
    ):
        ai_charts = ai_result["computed_charts"]
        keys = ["primary", "secondary", "tertiary", "quaternary"]
        ai_chart_dict = {}
        for i, key in enumerate(keys):
            if i < len(ai_charts):
                c = ai_charts[i]
                ai_chart_dict[key] = {
                    "labels": c.get("labels", []),
                    "values": c.get("values", []),
                    "label": c.get("title", key),
                    "chart_type": c.get("type", "bar"),
                }
            else:
                ai_chart_dict[key] = {"labels": [], "values": [], "label": "", "chart_type": "bar"}
        analytics_payload = dict(analytics_payload)
        analytics_payload["charts"] = ai_chart_dict

        # Also use AI KPIs if available
        if ai_result.get("computed_kpis"):
            analytics_payload["kpis"] = ai_result["computed_kpis"]

        # Use AI domain name and insights
        if ai_result.get("domain") and ai_result.get("confidence", 0) >= 50:
            analytics_payload["domain"] = {
                "name": ai_result["domain"],
                "confidence": round(ai_result["confidence"] / 100, 2),
            }
        if ai_result.get("insights"):
            analytics_payload["insights"] = ai_result["insights"]

    recent_uploads = database_service.fetch_all(
        """
        select id, file_name, domain_name, confidence, row_count, created_at
        from smartbi_uploads
        order by created_at desc
        limit 10
        """
    )

    dashboard = {
        "recent_uploads": recent_uploads,
        "latest_report": upload,
        "dataset_information": {
            "row_count": upload.get("row_count", 0),
            "column_count": analytics_payload.get("column_count", 0),
            "source_file": upload.get("file_name"),
        },
        "domain_detection": analytics_payload.get("domain", {}),
        "last_refresh_time": upload.get("created_at"),
        "record_count": upload.get("row_count", 0),
    }

    return jsonify({
        "upload": upload,
        "analytics": analytics_payload,
        "dashboard": dashboard,
    }), 200


@analytics_bp.get("/filter")
@login_required
def analytics_filter() -> tuple[dict[str, object], int]:
    upload, rows = get_analytics_context()
    if not upload:
        return jsonify({"message": "No analytics data available."}), 404

    filters, errors = parse_filter_parameters(request.args)
    if errors:
        return jsonify({"message": "Invalid filter parameters.", "errors": errors}), 400

    filtered_rows = apply_filters(rows, filters)
    response = build_analytics_response_from_dataset(upload, filtered_rows, applied_filters=filters)
    return jsonify(response), 200


@analytics_bp.get("/drilldown")
@login_required
def analytics_drilldown() -> tuple[dict[str, object], int]:
    upload, rows = get_analytics_context()
    if not upload:
        return jsonify({"message": "No analytics data available."}), 404

    parameters, errors = parse_drilldown_parameters(request.args)
    if errors:
        return jsonify({"message": "Invalid drill-down parameters.", "errors": errors}), 400

    drilldown_rows, drilldown = build_drilldown_result(rows, parameters)
    analysis = analyze_dataset(drilldown_rows)
    return jsonify({
        "upload": upload,
        "domain": analysis["domain"],
        "drilldown": drilldown,
        "columns": extract_columns(drilldown_rows),
        "rows": drilldown_rows,
        "analytics": {
            "row_count": analysis["row_count"],
            "column_count": analysis["column_count"],
            "kpis": analysis["kpis"],
            "charts": analysis["charts"],
            "insights": analysis["insights"],
        },
    }), 200


@analytics_bp.get("/compare")
@login_required
def analytics_compare() -> tuple[dict[str, object], int]:
    parameters, errors = parse_comparison_parameters(request.args)
    if errors:
        return jsonify({"message": "Invalid comparison parameters.", "errors": errors}), 400

    database_service = DatabaseService(current_app.config["DATABASE_URL"])
    try:
        response = compare_uploads(
            database_service,
            int(parameters["upload_a"]),
            int(parameters["upload_b"]),
            include_charts=bool(parameters["chart"]),
            summary_only=bool(parameters["summary_only"]),
        )
    except ComparisonError as error:
        payload: dict[str, object] = {"message": error.message}
        if error.errors:
            payload["errors"] = error.errors
        return jsonify(payload), error.status_code

    return jsonify(response), 200


@analytics_bp.get("/domain")
@login_required
def analytics_domain() -> tuple[dict[str, object], int]:
    upload, rows = get_analytics_context()
    if not upload:
        return jsonify({"message": "No analytics data available."}), 404
    analysis = analyze_dataset(rows)
    return jsonify({"domain": analysis["domain"], "upload": upload}), 200


@analytics_bp.get("/ai")
@login_required
def analytics_ai() -> tuple[dict[str, object], int]:
    """Run OpenRouter AI on the upload to get domain + visualizations with real data."""
    upload, rows = get_analytics_context()
    if not upload:
        return jsonify({"message": "No data available."}), 404
    column_names = list(rows[0].keys()) if rows else []
    ai_result = detect_domain_ai(column_names, rows[:5], all_rows=rows)
    return jsonify({"upload": upload, "ai": ai_result}), 200


@analytics_bp.get("/kpis")
@login_required
def analytics_kpis() -> tuple[dict[str, object], int]:
    response, status_code = build_analytics_response()
    if status_code != 200 or response is None:
        return jsonify({"message": "No analytics data available."}), status_code
    return jsonify({"domain": response["domain"], "kpis": response["kpis"]}), 200


@analytics_bp.get("/charts")
@login_required
def analytics_charts() -> tuple[dict[str, object], int]:
    response, status_code = build_analytics_response()
    if status_code != 200 or response is None:
        return jsonify({"message": "No analytics data available."}), status_code
    return jsonify({"domain": response["domain"], "charts": response["charts"]}), 200


# ── POST endpoints ────────────────────────────────────────────────────────────

@analytics_bp.post("/summary")
@login_required
def analytics_summary() -> tuple[dict[str, object], int]:
    payload = request.get_json(silent=True) or {}
    rows = payload.get("rows", [])
    return jsonify({"summary": calculate_summary_metrics(rows)}), 200


@analytics_bp.post("/rankings")
@login_required
def analytics_rankings() -> tuple[dict[str, object], int]:
    payload = request.get_json(silent=True) or {}
    rows = payload.get("rows", [])
    value_field = str(payload.get("value_field", "value"))
    return jsonify({"rankings": calculate_rankings(rows, value_field)}), 200


@analytics_bp.post("/percentages")
@login_required
def analytics_percentages() -> tuple[dict[str, object], int]:
    payload = request.get_json(silent=True) or {}
    rows = payload.get("rows", [])
    field_name = str(payload.get("field_name", "category"))
    return jsonify({"percentages": calculate_percentages(rows, field_name)}), 200


@analytics_bp.post("/trends")
@login_required
def analytics_trends() -> tuple[dict[str, object], int]:
    payload = request.get_json(silent=True) or {}
    rows = payload.get("rows", [])
    date_field = str(payload.get("date_field", "date"))
    value_field = str(payload.get("value_field", "value"))
    return jsonify({"trends": calculate_trends(rows, date_field, value_field)}), 200


@analytics_bp.post("/chat")
@login_required
def analytics_chat() -> tuple[dict[str, object], int]:
    from app.services.chat_service import chat_with_dataset
    
    payload = request.get_json(silent=True) or {}
    upload_id = payload.get("upload_id")
    message = payload.get("message")
    
    if not upload_id or not message:
        return jsonify({"message": "upload_id and message are required."}), 400
        
    database_service = DatabaseService(current_app.config["DATABASE_URL"])
    try:
        response_text = chat_with_dataset(int(upload_id), str(message), database_service)
        return jsonify({"response": response_text}), 200
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500
