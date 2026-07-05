from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from app.services.auth_service import login_required
from app.services.database_service import DatabaseService

history_bp = Blueprint("history", __name__)


def get_database_service() -> DatabaseService:
    return DatabaseService(current_app.config["DATABASE_URL"])


@history_bp.get("/")
@login_required
def history_index() -> tuple[dict[str, object], int]:
    return jsonify({"items": []}), 200


@history_bp.get("/uploads")
@login_required
def upload_history() -> tuple[dict[str, object], int]:
    database_service = get_database_service()
    rows = database_service.fetch_all(
        """
        select id, file_name, domain_name, confidence, row_count, summary_json, created_at
        from smartbi_uploads
        order by created_at desc
        """
    )
    return jsonify({"items": rows}), 200