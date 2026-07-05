from __future__ import annotations

from io import BytesIO

import pandas as pd

from app import create_app
from app.config import Config


class UploadTestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin123"


def build_excel_file(dataframe: pd.DataFrame) -> BytesIO:
    buffer = BytesIO()
    dataframe.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer


def test_upload_workflow_returns_validation_feedback(tmp_path, monkeypatch) -> None:
    app = create_app(UploadTestConfig)
    app.config.update(
        UPLOAD_FOLDER=str(tmp_path / "uploads"),
        CLEANED_FOLDER=str(tmp_path / "cleaned"),
        ORIGINAL_FOLDER=str(tmp_path / "original"),
        PROCESSED_FOLDER=str(tmp_path / "processed"),
        DATABASE_URL="postgresql://localhost/smartbi",
    )

    monkeypatch.setattr("app.blueprints.uploads.get_database_service", lambda: None)

    workbook = pd.DataFrame(
        [
            {"Candidate Name": "Asha", "Interview Date": "2026-01-01", "Offer CTC": 12.5},
            {"Candidate Name": "Asha", "Interview Date": "invalid-date", "Offer CTC": "oops"},
        ]
    )

    with app.test_client() as client:
        login_response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert login_response.status_code == 200

        response = client.post(
            "/api/uploads/",
            data={"files": (build_excel_file(workbook), "placement.xlsx")},
            content_type="multipart/form-data",
        )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload is not None
    assert payload["items"][0]["status"] == "validation_failed"
    assert any("Invalid date" in error for error in payload["items"][0]["errors"])