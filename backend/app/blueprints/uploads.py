from __future__ import annotations

import logging
import signal
from contextlib import contextmanager
from io import BytesIO

from flask import Blueprint, current_app, jsonify, request

from app.services.auth_service import login_required
from app.services.database_service import DatabaseService
from app.services.file_service import allowed_file
from app.services.processing_service import process_excel_file

uploads_bp = Blueprint("uploads", __name__)
logger = logging.getLogger(__name__)

# Per-file processing budget in seconds.
# Must be well under gunicorn --timeout (180s) to allow a clean JSON response.
_PROCESSING_TIMEOUT_SECONDS = 90


@contextmanager
def _processing_timeout(seconds: int):
    """Raise TimeoutError if the block takes longer than *seconds*."""
    def _handler(signum, frame):
        raise TimeoutError(f"Processing exceeded {seconds}s time limit.")
    old = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def get_database_service() -> DatabaseService:
    return DatabaseService(current_app.config["DATABASE_URL"])


@uploads_bp.get("/")
@login_required
def list_uploads() -> tuple[dict[str, object], int]:
    # Fetch upload metadata from the database
    database_service = get_database_service()
    uploads = database_service.fetch_all(
        """
        SELECT id, file_name, domain_name, confidence, row_count, created_at
        FROM smartbi_uploads
        ORDER BY created_at DESC
        """
    )
    return jsonify({"items": uploads}), 200


@uploads_bp.post("/")
@login_required
def upload_files() -> tuple[dict[str, object], int]:
    from flask import session

    uploaded_files = request.files.getlist("files")
    if not uploaded_files:
        return jsonify({"message": "No files were provided."}), 400

    database_service = get_database_service()
    user_id = session.get("user_id")
    results: list[dict[str, object]] = []

    for uploaded_file in uploaded_files:
        if not uploaded_file.filename or not allowed_file(uploaded_file.filename, current_app.config["ALLOWED_EXTENSIONS"]):
            results.append({"file_name": uploaded_file.filename, "status": "rejected", "reason": "Invalid file type."})
            continue

        try:
            # Read file into memory — avoids any disk I/O on ephemeral/read-only
            # filesystems such as Render's free tier.
            file_stream = BytesIO(uploaded_file.read())
            logger.info("Processing upload (in-memory): %s", uploaded_file.filename)

            with _processing_timeout(_PROCESSING_TIMEOUT_SECONDS):
                processing_result = process_excel_file(
                    file_stream,
                    uploaded_file.filename,
                    database_service,
                    cleaned_folder=None,   # no local disk writes on cloud deployment
                    user_id=user_id,
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
        except TimeoutError as exc:
            logger.error("Upload timed out for %s: %s", uploaded_file.filename, exc)
            results.append(
                {
                    "file_name": uploaded_file.filename,
                    "status": "error",
                    "reason": "Processing timed out. Try a smaller file or try again.",
                    "errors": ["Request timed out during processing."],
                    "warnings": [],
                    "domain_name": "Unknown",
                    "confidence": 0,
                    "row_count": 0,
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