from app import create_app
from app.config import Config
from app.services.database_service import DatabaseService


class DrilldownApiConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin123"
    DATABASE_URL = "postgresql://localhost/smartbi"


def _login(client) -> None:
    login_response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert login_response.status_code == 200


def _patch_upload(monkeypatch, rows, domain_name="Placement Management"):
    upload = {
        "id": 1,
        "file_name": "dataset.xlsx",
        "domain_name": domain_name,
        "confidence": 0.91,
        "row_count": len(rows),
        "summary_json": {},
        "created_at": "2026-01-01T00:00:00",
    }
    monkeypatch.setattr(DatabaseService, "fetch_upload_dataset", lambda self, upload_id=None: (upload, rows))
    return upload


def test_drilldown_api_returns_rows_for_dimension_click(monkeypatch) -> None:
    rows = [
        {"Candidate Name": "Asha", "Company": "TechNova", "Department": "CSE", "Status": "Selected", "Offer CTC": 12.5},
        {"Candidate Name": "Ben", "Company": "CloudPeak", "Department": "ECE", "Status": "Placed", "Offer CTC": 14.0},
        {"Candidate Name": "Mira", "Company": "TechNova", "Department": "IT", "Status": "Selected", "Offer CTC": 11.0},
    ]
    _patch_upload(monkeypatch, rows)

    app = create_app(DrilldownApiConfig)
    with app.test_client() as client:
        _login(client)
        response = client.get("/api/analytics/drilldown?field=company&value=TechNova")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload is not None
    assert payload["drilldown"]["type"] == "dimension"
    assert payload["drilldown"]["matched_row_count"] == 2
    assert payload["drilldown"]["returned_row_count"] == 2
    assert payload["analytics"]["kpis"]["total_students"] == 2
    assert {row["Candidate Name"] for row in payload["rows"]} == {"Asha", "Mira"}
    assert "Company" in payload["columns"]


def test_drilldown_api_returns_rows_for_low_stock_metric(monkeypatch) -> None:
    rows = [
        {"Product": "Keyboard", "Category": "Accessories", "Stock Qty": 4, "Reorder Level": 5, "Unit Price": 25},
        {"Product": "Monitor", "Category": "Displays", "Stock Qty": 12, "Reorder Level": 5, "Unit Price": 150},
        {"Product": "Mouse", "Category": "Accessories", "Stock Qty": 0, "Reorder Level": 3, "Unit Price": 15},
    ]
    _patch_upload(monkeypatch, rows, domain_name="Inventory")

    app = create_app(DrilldownApiConfig)
    with app.test_client() as client:
        _login(client)
        response = client.get("/api/analytics/drilldown?metric=low_stock&limit=1")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload is not None
    assert payload["drilldown"]["type"] == "metric"
    assert payload["drilldown"]["target"] == "low_stock"
    assert payload["drilldown"]["matched_row_count"] == 2
    assert payload["drilldown"]["returned_row_count"] == 1
    assert payload["drilldown"]["has_more"] is True
    assert payload["rows"][0]["Product"] == "Keyboard"


def test_drilldown_api_rejects_invalid_parameters(monkeypatch) -> None:
    _patch_upload(monkeypatch, [{"Company": "TechNova"}])

    app = create_app(DrilldownApiConfig)
    with app.test_client() as client:
        _login(client)
        response = client.get("/api/analytics/drilldown?field=company&limit=999")

    assert response.status_code == 400
    payload = response.get_json()
    assert payload is not None
    assert payload["message"] == "Invalid drill-down parameters."
    assert "Provide a value/label when drilling into a field or dimension." in payload["errors"]
    assert "limit must be between 1 and 500." in payload["errors"]


def test_drilldown_api_returns_404_for_missing_upload(monkeypatch) -> None:
    monkeypatch.setattr(DatabaseService, "fetch_upload_dataset", lambda self, upload_id=None: (None, []))

    app = create_app(DrilldownApiConfig)
    with app.test_client() as client:
        _login(client)
        response = client.get("/api/analytics/drilldown?field=company&value=TechNova")

    assert response.status_code == 404
