from flask import Flask, jsonify
from flask_cors import CORS
import os

from pathlib import Path
from flask import send_from_directory

from app.blueprints.analytics import analytics_bp
from app.blueprints.auth import auth_bp
from app.blueprints.history import history_bp
from app.blueprints.reports import reports_bp
from app.blueprints.uploads import uploads_bp
from app.config import Config
from app.extensions import init_logging


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"message": "Bad request.", "details": str(error)}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"message": "Unauthorized.", "details": str(error)}), 401
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({"message": "File too large.", "details": "Maximum upload size exceeded."}), 413

    @app.errorhandler(500)
    def server_error(error):
        app.logger.error(f"Internal server error: {error}")
        return jsonify({"message": "Internal server error.", "details": str(error)}), 500


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_class)
    frontend_root = Path(__file__).resolve().parents[2] / "frontend"
    
    # Initialize configuration
    config_class.init_app()

    allowed_origin = os.getenv('SMARTBI_FRONTEND_URL', '*')
    init_logging(app)
    # Apply CORS after app creation
    CORS(app, resources={r"/api/*": {"origins": allowed_origin}}, supports_credentials=True)

    # Register static file routes FIRST
    @app.get("/favicon.ico")
def favicon():
    return send_from_directory(frontend_root, "favicon.ico")

    @app.get("/assets/<path:filename>")
    def frontend_assets(filename: str) -> object:
        return send_from_directory(frontend_root / "assets", filename)
    
    @app.get("/")
    def home() -> object:
        return send_from_directory(frontend_root, "index.html")

    @app.get("/upload")
    def upload_page() -> object:
        return send_from_directory(frontend_root / "pages", "upload.html")

    @app.get("/dashboard")
    def dashboard_page() -> object:
        return send_from_directory(frontend_root / "pages", "dashboard.html")

    @app.get("/reports")
    def reports_page() -> object:
        return send_from_directory(frontend_root / "pages", "reports.html")

    @app.get("/compare")
    def compare_page() -> object:
        return send_from_directory(frontend_root / "pages", "compare.html")

    @app.get("/home")
    def home_page() -> object:
        return send_from_directory(frontend_root / "pages", "home.html")

    @app.get("/history")
    def history_page() -> object:
        return send_from_directory(frontend_root / "pages", "history.html")
    
    @app.get("/api/health")
    def health_check() -> tuple[dict[str, str], int]:
        return jsonify({"status": "ok", "service": "SmartBI"}), 200

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(uploads_bp, url_prefix="/api/uploads")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    app.register_blueprint(reports_bp, url_prefix="/api/reports")
    app.register_blueprint(history_bp, url_prefix="/api/history")
    
    # Register error handlers LAST
    register_error_handlers(app)

    return app