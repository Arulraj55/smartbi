from app import create_app
from app.config import Config
from app.services.database_service import DatabaseService


class AnalyticsApiConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin123"
    DATABASE_URL = "postgresql://localhost/smartbi"


def test_analytics_summary_api_returns_structured_json(monkeypatch) -> None:
    rows = [
        {"Candidate Name": "Asha", "Company": "TechNova", "Department": "CSE", "Gender": "F", "Interview Date": "2026-01-01", "Offer CTC": 12.5, "Status": "Selected", "Year": 2026},
        {"Candidate Name": "Ben", "Company": "CloudPeak", "Department": "ECE", "Gender": "M", "Interview Date": "2026-01-15", "Offer CTC": 14.0, "Status": "Selected", "Year": 2026},
    ]

    monkeypatch.setattr(DatabaseService, "fetch_latest_upload", lambda self: {"id": 1, "file_name": "placement.xlsx", "domain_name": "Placement Management", "confidence": 0.9, "row_count": 2, "summary_json": {}, "created_at": "2026-01-01T00:00:00"})
    monkeypatch.setattr(DatabaseService, "fetch_upload_by_id", lambda self, upload_id: {"id": upload_id, "file_name": "placement.xlsx", "domain_name": "Placement Management", "confidence": 0.9, "row_count": 2, "summary_json": {}, "created_at": "2026-01-01T00:00:00"})
    monkeypatch.setattr(DatabaseService, "fetch_upload_rows", lambda self, upload_id: rows)

    app = create_app(AnalyticsApiConfig)
    with app.test_client() as client:
        login_response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        assert login_response.status_code == 200

        response = client.get("/api/analytics/summary")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload is not None
    assert payload["domain"]["name"] == "Placement Management"
    assert payload["kpis"]["total_students"] == 2
    assert payload["charts"]["primary"]["labels"]


def test_analytics_api_handles_missing_upload(monkeypatch) -> None:
    monkeypatch.setattr(DatabaseService, "fetch_latest_upload", lambda self: None)
    monkeypatch.setattr(DatabaseService, "fetch_upload_dataset", lambda self, upload_id=None: (None, []))

    app = create_app(AnalyticsApiConfig)
    with app.test_client() as client:
        login_response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        assert login_response.status_code == 200

        response = client.get("/api/analytics/summary?upload_id=999")

    assert response.status_code == 404