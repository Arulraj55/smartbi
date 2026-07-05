from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request, session
import hashlib

auth_bp = Blueprint("auth", __name__)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@auth_bp.post("/signup")
def signup() -> tuple[dict[str, object], int]:
    from app.services.database_service import DatabaseService
    
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    email = str(payload.get("email", "")).strip()
    password = str(payload.get("password", ""))
    full_name = str(payload.get("full_name", "")).strip()

    if not username or not email or not password:
        return jsonify({"message": "Username, email, and password are required."}), 400

    if len(password) < 6:
        return jsonify({"message": "Password must be at least 6 characters."}), 400

    db = DatabaseService(current_app.config["DATABASE_URL"])
    
    # Check if username or email exists
    existing = db.fetch_one("SELECT id FROM smartbi_users WHERE username = %s OR email = %s", (username, email))
    if existing:
        return jsonify({"message": "Username or email already exists."}), 409

    # Insert new user
    password_hash = hash_password(password)
    db.execute(
        "INSERT INTO smartbi_users (username, email, password_hash, full_name) VALUES (%s, %s, %s, %s)",
        (username, email, password_hash, full_name)
    )
    
    return jsonify({"message": "Account created successfully. Please login."}), 201


@auth_bp.post("/login")
def login() -> tuple[dict[str, object], int]:
    from app.services.database_service import DatabaseService
    
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", ""))
    password = str(payload.get("password", ""))

    # Check database users ONLY
    db = DatabaseService(current_app.config["DATABASE_URL"])
    user = db.fetch_one(
        "SELECT id, username, password_hash, is_active FROM smartbi_users WHERE username = %s",
        (username,)
    )
    
    if not user or not user["is_active"]:
        return jsonify({"message": "Invalid credentials."}), 401
    
    password_hash = hash_password(password)
    if user["password_hash"] != password_hash:
        return jsonify({"message": "Invalid credentials."}), 401

    session["is_admin_authenticated"] = True
    session["admin_username"] = user["username"]
    session["user_id"] = user["id"]
    return jsonify({"message": "Login successful.", "user": user["username"]}), 200


@auth_bp.post("/logout")
def logout() -> tuple[dict[str, object], int]:
    session.clear()
    return jsonify({"message": "Logged out."}), 200