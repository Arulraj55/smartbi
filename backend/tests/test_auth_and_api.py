from app import create_app
from app.config import Config


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin123"
    DATABASE_URL = "postgresql://localhost/smartbi"


def test_protected_route_requires_login() -> None:
    app = create_app(TestConfig)

    with app.test_client() as client:
        unauthenticated_response = client.get("/api/uploads/")
        assert unauthenticated_response.status_code == 401

        login_response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert login_response.status_code == 200

        authenticated_response = client.get("/api/uploads/")
        assert authenticated_response.status_code == 200