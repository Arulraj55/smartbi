from __future__ import annotations

import os
from pathlib import Path


class Config:
    """Application configuration class."""
    
    SECRET_KEY = os.getenv("SMARTBI_SECRET_KEY", "change-me-in-production")
    DATABASE_URL = os.getenv("SMARTBI_DATABASE_URL", "postgresql://localhost/smartbi")
    UPLOAD_FOLDER = os.getenv("SMARTBI_UPLOAD_FOLDER", "backend/uploads")
    CLEANED_FOLDER = os.getenv("SMARTBI_CLEANED_FOLDER", "backend/cleaned")
    PROCESSED_FOLDER = os.getenv("SMARTBI_PROCESSED_FOLDER", "backend/processed")
    ORIGINAL_FOLDER = os.getenv("SMARTBI_ORIGINAL_FOLDER", "backend/original")
    ALLOWED_EXTENSIONS = {"xlsx", "xls"}
    MAX_CONTENT_LENGTH = int(os.getenv("SMARTBI_MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
    ADMIN_USERNAME = os.getenv("SMARTBI_ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("SMARTBI_ADMIN_PASSWORD", "admin123")
    
    # Session configuration — SECURE must be True on HTTPS (Render/production)
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = int(os.getenv("SMARTBI_SESSION_LIFETIME", str(3600)))
    
    # Ensure upload directories exist (best-effort; skipped on read-only filesystems)
    @classmethod
    def init_app(cls):
        """Initialize application directories (no-op on ephemeral/read-only deployments)."""
        for folder in [cls.UPLOAD_FOLDER, cls.CLEANED_FOLDER, cls.PROCESSED_FOLDER, cls.ORIGINAL_FOLDER]:
            try:
                Path(folder).mkdir(parents=True, exist_ok=True)
            except OSError:
                pass  # read-only or ephemeral filesystem — disk storage not used in cloud mode