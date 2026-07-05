from app import create_app
from app.config import Config
from app.services.comparison_service import calculate_metric_change
from app.services.database_service import DatabaseService


class ComparisonApiConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin123"
    DATABASE_URL = "postgresql://localhost/smartbi"


def _login(client) -> None:
    login_response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert login_response.status_code == 200


def _patch_uploads(monkeypatch, datasets):
    def fetch_upload_dataset(self, upload_id=None):
        item = datasets.get(upload_id)
        if item is None:
            return None, []
        return item["upload"], item["rows"]

    monkeypatch.setattr(DatabaseService, "fetch_upload_dataset", fetch_upload_dataset)


def _upload(upload_id, file_name, domain_name, rows):
    return {
        "upload": {
            "id": upload_id,
            "file_name": file_name,
            "domain_name": domain_name,
            "confidence": 0.91,
            "row_count": len(rows),
            "summary_json": {},
            "created_at": "2026-01-01T00:00:00",
        },
        "rows": rows,
    }


def test_compare_api_returns_successful_sales_comparison(monkeypatch) -> None:
    old_rows = [
        {"Order ID": "A1", "Order Date": "2026-01-01", "Customer": "Nia", "Product": "Laptop", "Region": "West", "Revenue Amount": 1000},
        {"Order ID": "A2", "Order Date": "2026-01-02", "Customer": "Dev", "Product": "Mouse", "Region": "East", "Revenue Amount": 500},
    ]
    new_rows = [
        {"Order ID": "B1", "Order Date": "2026-02-01", "Customer": "Nia", "Product": "Laptop", "Region": "West", "Revenue Amount": 1200},
        {"Order ID": "B2", "Order Date": "2026-02-02", "Customer": "Mira", "Product": "Keyboard", "Region": "South", "Revenue Amount": 900},
        {"Order ID": "B3", "Order Date": "2026-02-03", "Customer": "Dev", "Product": "Mouse", "Region": "East", "Revenue Amount": 300},
    ]
    _patch_uploads(monkeypatch, {
        1: _upload(1, "sales_old.xlsx", "Retail Sales", old_rows),
        2: _upload(2, "sales_new.xlsx", "Retail Sales", new_rows),
    })

    app = create_app(ComparisonApiConfig)
    with app.test_client() as client:
        _login(client)
        response = client.get("/api/analytics/compare?upload_a=1&upload_b=2")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload is not None
    assert payload["domain"] == "Retail Sales"
    assert payload["comparison"]["total_revenue"]["old"] == 1500
    assert payload["comparison"]["total_revenue"]["new"] == 2400
    assert payload["comparison"]["total_revenue"]["difference"] == 900
    assert payload["comparison"]["total_orders"]["trend"] == "Increase"
    assert payload["charts"] == {}


def test_compare_api_rejects_domain_mismatch(monkeypatch) -> None:
    placement_rows = [{"Candidate Name": "Asha", "Company": "TechNova", "Offer CTC": 12.5, "Status": "Selected"}]
    inventory_rows = [{"Product": "Keyboard", "Stock Qty": 4, "Reorder Level": 5, "SKU": "KBD-1"}]
    _patch_uploads(monkeypatch, {
        1: _upload(1, "placement.xlsx", "Placement Management", placement_rows),
        2: _upload(2, "inventory.xlsx", "Inventory", inventory_rows),
    })

    app = create_app(ComparisonApiConfig)
    with app.test_client() as client:
        _login(client)
        response = client.get("/api/analytics/compare?upload_a=1&upload_b=2")

    assert response.status_code == 400
    payload = response.get_json()
    assert payload is not None
    assert payload["message"] == "Uploads must have matching domains."
    assert any("Placement Management" in error for error in payload["errors"])
    assert any("Inventory" in error for error in payload["errors"])


def test_compare_api_returns_404_for_missing_upload(monkeypatch) -> None:
    rows = [{"Order ID": "A1", "Customer": "Nia", "Revenue Amount": 1000}]
    _patch_uploads(monkeypatch, {1: _upload(1, "sales.xlsx", "Retail Sales", rows)})

    app = create_app(ComparisonApiConfig)
    with app.test_client() as client:
        _login(client)
        response = client.get("/api/analytics/compare?upload_a=1&upload_b=99")

    assert response.status_code == 404
    payload = response.get_json()
    assert payload is not None
    assert payload["message"] == "One or more uploads do not exist."
    assert payload["errors"] == ["upload_b"]


def test_compare_api_rejects_empty_dataset(monkeypatch) -> None:
    rows = [{"Order ID": "A1", "Customer": "Nia", "Revenue Amount": 1000}]
    _patch_uploads(monkeypatch, {
        1: _upload(1, "sales.xlsx", "Retail Sales", rows),
        2: _upload(2, "empty.xlsx", "Retail Sales", []),
    })

    app = create_app(ComparisonApiConfig)
    with app.test_client() as client:
        _login(client)
        response = client.get("/api/analytics/compare?upload_a=1&upload_b=2")

    assert response.status_code == 400
    payload = response.get_json()
    assert payload is not None
    assert payload["message"] == "One or more uploads are empty."
    assert payload["errors"] == ["upload_b"]


def test_growth_calculation_handles_increase_decrease_and_no_change() -> None:
    increase = calculate_metric_change(100, 125)
    decrease = calculate_metric_change(100, 75)
    no_change = calculate_metric_change(50, 50)
    zero_old = calculate_metric_change(0, 20)

    assert increase["growth_percent"] == 25
    assert increase["trend"] == "Increase"
    assert decrease["growth_percent"] == -25
    assert decrease["trend"] == "Decrease"
    assert no_change["growth_percent"] == 0
    assert no_change["trend"] == "No Change"
    assert zero_old["growth_percent"] == 100


def test_compare_api_returns_chart_payload(monkeypatch) -> None:
    old_rows = [{"Product": "Keyboard", "Stock Qty": 4, "Reorder Level": 5, "Unit Price": 25, "Supplier": "A"}]
    new_rows = [
        {"Product": "Keyboard", "Stock Qty": 8, "Reorder Level": 5, "Unit Price": 25, "Supplier": "A"},
        {"Product": "Monitor", "Stock Qty": 2, "Reorder Level": 3, "Unit Price": 150, "Supplier": "B"},
    ]
    _patch_uploads(monkeypatch, {
        1: _upload(1, "inventory_old.xlsx", "Inventory", old_rows),
        2: _upload(2, "inventory_new.xlsx", "Inventory", new_rows),
    })

    app = create_app(ComparisonApiConfig)
    with app.test_client() as client:
        _login(client)
        response = client.get("/api/analytics/compare?upload_a=1&upload_b=2&chart=true")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload is not None
    assert payload["charts"]["bar_chart"]["labels"]
    assert len(payload["charts"]["bar_chart"]["datasets"]) == 2
    assert payload["charts"]["line_chart"]["datasets"]
    assert payload["charts"]["comparison_chart"]["old_values"]
    assert payload["charts"]["trend_chart"]["label"] == "Growth %"


def test_compare_api_rejects_missing_parameters() -> None:
    app = create_app(ComparisonApiConfig)
    with app.test_client() as client:
        _login(client)
        response = client.get("/api/analytics/compare?upload_a=1")

    assert response.status_code == 400
    payload = response.get_json()
    assert payload is not None
    assert payload["message"] == "Invalid comparison parameters."
    assert payload["errors"] == ["upload_b is required."]
