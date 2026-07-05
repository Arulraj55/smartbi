from __future__ import annotations

from functools import wraps

from flask import jsonify, session


def login_required(view_function):
    @wraps(view_function)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin_authenticated"):
            return jsonify({"message": "Authentication required."}), 401
        return view_function(*args, **kwargs)

    return wrapped