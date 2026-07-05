from app import create_app
from app.config import Config
from app.services.database_service import DatabaseService


class DashboardApiConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin123"
    DATABASE_URL = "postgresql://localhost/smartbi"


def test_dashboard_api_returns_dashboard_payload(monkeypatch) -> None:
    upload = {
        "id": 1,
        "file_name": "placement.xlsx",
        "domain_name": "Placement Management",
        "confidence": 0.91,
        "row_count": 2,
        "summary_json": {},
        "created_at": "2026-01-01T00:00:00",
    }
    rows = [
        {"Candidate Name": "Asha", "Company": "TechNova", "Department": "CSE", "Gender": "F", "Interview Date": "2026-01-01", "Offer CTC": 12.5, "Status": "Selected", "Year": 2026},
        {"Candidate Name": "Ben", "Company": "CloudPeak", "Department": "ECE", "Gender": "M", "Interview Date": "2026-01-15", "Offer CTC": 14.0, "Status": "Placed", "Year": 2026},
    ]

    monkeypatch.setattr(DatabaseService, "fetch_upload_dataset", lambda self, upload_id=None: (upload, rows))
    monkeypatch.setattr(DatabaseService, "fetch_all", lambda self, query, parameters=None: [upload])

    app = create_app(DashboardApiConfig)
    with app.test_client() as client:
        login_response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        assert login_response.status_code == 200

        response = client.get("/api/analytics/dashboard")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload is not None
    assert payload["dashboard"]["record_count"] == 2
    assert payload["analytics"]["domain"]["name"] == "Placement Management"


def test_dashboard_api_returns_404_for_missing_data(monkeypatch) -> None:
    monkeypatch.setattr(DatabaseService, "fetch_upload_dataset", lambda self, upload_id=None: (None, []))

    app = create_app(DashboardApiConfig)
    with app.test_client() as client:
        login_response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        assert login_response.status_code == 200

        response = client.get("/api/analytics/dashboard?upload_id=999")

    assert response.status_code == 404