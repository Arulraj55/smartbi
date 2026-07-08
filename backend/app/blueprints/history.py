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
    from flask import session
    database_service = get_database_service()
    user_id = session.get("user_id")
    rows = database_service.fetch_uploads_for_user(user_id)
    return jsonify({"items": rows}), 200