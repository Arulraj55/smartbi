from __future__ import annotations

from io import BytesIO

from flask import Blueprint, current_app, jsonify, request, send_file
from werkzeug.datastructures import MultiDict

from app.services.auth_service import login_required
from app.services.analytics_service import calculate_summary_metrics
from app.services.database_service import DatabaseService
from app.services.filter_service import parse_filter_parameters
from app.services.report_service import ReportError, generate_report, report_metadata

reports_bp = Blueprint("reports", __name__)


@reports_bp.get("")
@reports_bp.get("/")
@login_required
def reports_index() -> tuple[dict[str, object], int]:
    return jsonify(report_metadata()), 200


@reports_bp.get("/download")
@login_required
def report_download() -> object:
    from flask import session
    upload_id = request.args.get("upload_id", type=int)
    report_format = request.args.get("format", "")
    compare = str(request.args.get("compare", "")).strip().lower() in {"1", "true", "yes", "on"}
    upload_b = request.args.get("upload_b", type=int)

    errors = []
    if upload_id is None:
        errors.append("upload_id is required.")
    if not report_format:
        errors.append("format is required.")
    filters, filter_errors = parse_filter_parameters(_filter_args(request.args))
    errors.extend(filter_errors)
    if errors:
        return jsonify({"message": "Invalid report parameters.", "errors": errors}), 400

    user_id = session.get("user_id")
    database_service = DatabaseService(current_app.config["DATABASE_URL"])
    try:
        report_file = generate_report(
            database_service,
            int(upload_id),
            report_format,
            filters=filters,
            compare=compare,
            upload_b=upload_b,
            user_id=user_id,
        )
    except ReportError as error:
        payload: dict[str, object] = {"message": error.message}
        if error.errors:
            payload["errors"] = error.errors
        return jsonify(payload), error.status_code

    return send_file(
        BytesIO(report_file.content),
        mimetype=report_file.mimetype,
        as_attachment=True,
        download_name=report_file.filename,
    )


@reports_bp.post("/preview")
@login_required
def report_preview() -> tuple[dict[str, object], int]:
    payload = request.get_json(silent=True) or {}
    rows = payload.get("rows", [])
    return jsonify({"report": calculate_summary_metrics(rows)}), 200


def _filter_args(query_args) -> MultiDict:
    filtered_args = MultiDict(query_args)
    for key in ("format", "compare", "upload_b"):
        filtered_args.pop(key, None)
    return filtered_args
