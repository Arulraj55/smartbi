from __future__ import annotations

import logging

from flask import Blueprint, current_app, jsonify, request

from app.services.auth_service import login_required
from app.services.database_service import DatabaseService
from app.services.file_service import allowed_file, ensure_directories, save_uploaded_file
from app.services.processing_service import process_excel_file

uploads_bp = Blueprint("uploads", __name__)
logger = logging.getLogger(__name__)


def get_database_service() -> DatabaseService:
    return DatabaseService(current_app.config["DATABASE_URL"])


@uploads_bp.get("/")
@login_required
def list_uploads() -> tuple[dict[str, object], int]:
    return jsonify({"items": []}), 200


@uploads_bp.post("/")
@login_required
def upload_files() -> tuple[dict[str, object], int]:
    from flask import session
    
    uploaded_files = request.files.getlist("files")
    if not uploaded_files:
        return jsonify({"message": "No files were provided."}), 400

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    cleaned_folder = current_app.config["CLEANED_FOLDER"]
    original_folder = current_app.config["ORIGINAL_FOLDER"]
    processed_folder = current_app.config["PROCESSED_FOLDER"]
    ensure_directories(upload_folder, cleaned_folder, original_folder, processed_folder)

    database_service = get_database_service()
    user_id = session.get("user_id")
    results: list[dict[str, object]] = []

    for uploaded_file in uploaded_files:
        if not uploaded_file.filename or not allowed_file(uploaded_file.filename, current_app.config["ALLOWED_EXTENSIONS"]):
            results.append({"file_name": uploaded_file.filename, "status": "rejected", "reason": "Invalid file type."})
            continue

        try:
            saved_path = save_uploaded_file(uploaded_file, original_folder)
            logger.info("Processing upload: %s", saved_path)
            processing_result = process_excel_file(
                saved_path,
                uploaded_file.filename,
                database_service,
                current_app.config["CLEANED_FOLDER"],
                user_id,
            )
            results.append(
                {
                    "file_name": processing_result.file_name,
                    "status": "processed" if processing_result.validation.is_valid else "validation_failed",
                    "upload_id": processing_result.upload_id,
                    "domain_name": processing_result.domain_name,
                    "confidence": processing_result.confidence,
                    "row_count": processing_result.row_count,
                    "summary": processing_result.summary,
                    "columns": processing_result.columns,
                    "errors": processing_result.validation.errors,
                    "warnings": processing_result.validation.warnings,
                }
            )
        except Exception as exc:  # pragma: no cover - defensive logging path
            logger.exception("Upload processing failed for %s", uploaded_file.filename)
            results.append(
                {
                    "file_name": uploaded_file.filename,
                    "status": "error",
                    "reason": f"Processing error: {str(exc)}",
                    "errors": ["The workbook could not be processed. Please check the file format."],
                    "warnings": [],
                    "domain_name": "Unknown",
                    "confidence": 0,
                    "row_count": 0,
                }
            )

    return jsonify({"items": results}), 200