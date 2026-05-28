import functools

from flask import request, jsonify, g

from app.auth.helpers import verify_api_key, get_session_data, SCOPE_ALL


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        user_id = _resolve_user()
        if user_id is None:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            from flask import redirect, url_for
            return redirect(url_for("auth.login_page"))
        g.user_id = user_id
        return view(**kwargs)
    return wrapped_view


def api_key_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        result = _resolve_api_user()
        if result is None:
            return jsonify({"error": "Authentication required"}), 401
        g.user_id = result["user_id"]
        g.token_scopes = result["scopes"]
        g.api_key_tag = result.get("tag", "")
        return view(**kwargs)
    return wrapped_view


def require_scope(*scopes: str):
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            token_scopes = getattr(g, "token_scopes", "")
            token_set = set(s.strip() for s in token_scopes.split(",") if s.strip())
            if not token_set or not any(s in token_set for s in scopes):
                return jsonify({"error": "Insufficient permissions", "required_scopes": list(scopes)}), 403
            return view(**kwargs)
        return wrapped_view
    return decorator


def _resolve_user() -> int | None:
    session_id = request.cookies.get("sid")
    if session_id:
        data = get_session_data(session_id)
        if data and "user_id" in data:
            return data["user_id"]
    return None


def _resolve_api_user() -> dict | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        raw_key = auth_header[len("Bearer "):].strip()
        result = verify_api_key(raw_key)
        if result:
            return result

    return None
