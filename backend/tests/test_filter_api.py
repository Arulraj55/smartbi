from app import create_app
from app.config import Config
from app.services.database_service import DatabaseService


class FilterApiConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin123"
    DATABASE_URL = "postgresql://localhost/smartbi"


def _patch_upload(monkeypatch, rows):
    upload = {
        "id": 1,
        "file_name": "placement.xlsx",
        "domain_name": "Placement Management",
        "confidence": 0.91,
        "row_count": len(rows),
        "summary_json": {},
        "created_at": "2026-01-01T00:00:00",
    }
    monkeypatch.setattr(DatabaseService, "fetch_upload_dataset", lambda self, upload_id=None: (upload, rows))
    monkeypatch.setattr(DatabaseService, "fetch_all", lambda self, query, parameters=None: [upload])
    return upload


def test_filter_api_returns_filtered_analytics(monkeypatch) -> None:
    rows = [
        {"Candidate Name": "Asha", "Company": "TechNova", "Department": "CSE", "Gender": "F", "Interview Date": "2026-01-01", "Offer CTC": 12.5, "Status": "Selected", "Year": 2026},
        {"Candidate Name": "Ben", "Company": "CloudPeak", "Department": "ECE", "Gender": "M", "Interview Date": "2026-02-01", "Offer CTC": 14.0, "Status": "Placed", "Year": 2026},
    ]
    _patch_upload(monkeypatch, rows)

    app = create_app(FilterApiConfig)
    with app.test_client() as client:
        login_response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        assert login_response.status_code == 200

        response = client.get(
            "/api/analytics/filter?department=CSE&company=TechNova&year=2026&search_keyword=asha&start_date=2026-01-01&end_date=2026-01-31"
        )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload is not None
    assert payload["row_count"] == 1
    assert payload["filtered_row_count"] == 1
    assert payload["total_row_count"] == 2
    assert payload["filters"]["department"] == ["CSE"]
    assert payload["domain"]["name"] == "Placement Management"
    assert payload["kpis"]["total_students"] == 1


def test_filter_api_rejects_invalid_filters(monkeypatch) -> None:
    rows = [
        {"Candidate Name": "Asha", "Company": "TechNova", "Department": "CSE", "Gender": "F", "Interview Date": "2026-01-01", "Offer CTC": 12.5, "Status": "Selected", "Year": 2026},
    ]
    _patch_upload(monkeypatch, rows)

    app = create_app(FilterApiConfig)
    with app.test_client() as client:
        login_response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        assert login_response.status_code == 200

        response = client.get("/api/analytics/filter?start_date=invalid-date&year=abc&unsupported=value")

    assert response.status_code == 400
    payload = response.get_json()
    assert payload is not None
    assert payload["message"] == "Invalid filter parameters."
    assert len(payload["errors"]) >= 3


def test_filter_api_returns_empty_result_for_no_matches(monkeypatch) -> None:
    rows = [
        {"Candidate Name": "Asha", "Company": "TechNova", "Department": "CSE", "Gender": "F", "Interview Date": "2026-01-01", "Offer CTC": 12.5, "Status": "Selected", "Year": 2026},
    ]
    _patch_upload(monkeypatch, rows)

    app = create_app(FilterApiConfig)
    with app.test_client() as client:
        login_response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        assert login_response.status_code == 200

        response = client.get("/api/analytics/filter?department=ECE&company=CloudPeak")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload is not None
    assert payload["row_count"] == 0
    assert payload["filtered_row_count"] == 0
    assert payload["domain"]["name"] == "Generic"
    assert payload["kpis"]["row_count"] == 0