import secrets
import json
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash, check_password_hash

from app.container import db


SCOPE_ALL = "mail:send,mail:read,keys:manage"


def generate_api_key(scopes: str = "") -> tuple[str, str, str]:
    raw = secrets.token_hex(32)
    prefix = raw[:8]
    full_key = f"et_{prefix}_{raw}"
    key_hash = generate_password_hash(full_key)
    return full_key, prefix, key_hash


def verify_api_key(raw_key: str) -> dict | None:
    if not raw_key.startswith("et_") or raw_key.count("_") < 2:
        return None

    parts = raw_key.split("_", 2)
    prefix = parts[1]

    stored = db.get_api_key_by_prefix(prefix)
    if not stored:
        return None

    if not check_password_hash(stored["key_hash"], raw_key):
        return None

    db.update_api_key_used(stored["id"])
    return {
        "user_id": stored["user_id"],
        "scopes": stored.get("scopes", ""),
        "tag": stored.get("tag", ""),
    }


def create_session(user_id: int) -> str:
    session_id = secrets.token_hex(32)
    expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()
    db.create_session(session_id, user_id, json.dumps({"user_id": user_id}), expires_at)
    return session_id


def get_session_data(session_id: str) -> dict | None:
    sess = db.get_session(session_id)
    if not sess:
        return None
    return json.loads(sess["data"])


def destroy_session(session_id: str) -> None:
    if session_id:
        db.delete_session(session_id)
