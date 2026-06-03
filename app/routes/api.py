import logging
from flask import Blueprint, request, jsonify, abort, g

from app.auth.decorators import api_key_required, require_scope
from app.auth.helpers import generate_api_key
from app.container import db, storage
from app.limiter import limiter

bp = Blueprint("api", __name__, url_prefix="/api/v1")


# ── API Key management ───────────────────────────────────────────────────────


@bp.route("/api-keys", methods=["GET"])
@limiter.limit("30 per minute")
@api_key_required
@require_scope("keys:manage")
def list_api_keys():
    keys = db.get_api_keys_for_user(g.user_id)
    return jsonify({"api_keys": keys}), 200


@bp.route("/api-keys", methods=["POST"])
@limiter.limit("10 per minute")
@api_key_required
@require_scope("keys:manage")
def create_api_key():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    scopes = data.get("scopes", "mail:send,mail:read,keys:manage")
    tag = data.get("tag", "").strip()

    if not name:
        return jsonify({"error": "name is required"}), 400

    full_key, prefix, key_hash = generate_api_key(scopes)
    key_id = db.create_api_key(g.user_id, name, prefix, key_hash, scopes, tag)

    return jsonify({"id": key_id, "name": name, "token": full_key, "scopes": scopes, "tag": tag}), 201


@bp.route("/api-keys/<int:key_id>", methods=["DELETE"])
@limiter.limit("10 per minute")
@api_key_required
@require_scope("keys:manage")
def delete_api_key_endpoint(key_id):
    keys = db.get_api_keys_for_user(g.user_id)
    if not any(k["id"] == key_id for k in keys):
        abort(404)

    db.delete_api_key(key_id)
    return jsonify({"status": "ok"}), 200


# ── Incoming mail ────────────────────────────────────────────────────────────


@bp.route("/incoming-mail", methods=["POST"])
@limiter.limit("30 per minute")
@api_key_required
@require_scope("mail:send")
def incoming_mail():
    logging.getLogger("app").info("Size of request: %s", request.content_length)
    user_id = g.user_id
    api_key_tag = getattr(g, "api_key_tag", "")

    to_addr = request.form.get("to", "").strip().lower()
    from_addr = request.form.get("from", "").strip().lower()
    subject = request.form.get("subject", "")
    body_text = request.form.get("body_text", "")
    body_html = request.form.get("body_html", "")
    tag = request.headers.get("X-HEMT-Tag", "").strip() or api_key_tag

    if not to_addr or not from_addr:
        return jsonify({"error": "Missing required fields: to, from"}), 400

    msg_id = db.create_message(user_id, from_addr, to_addr, subject, body_text, body_html, tag)

    for key in request.files:
        for file in request.files.getlist(key):
            if file and file.filename:
                storage_path = storage.save(file.filename, file)
                db.create_attachment(
                    msg_id,
                    file.filename,
                    file.content_type or "application/octet-stream",
                    0,
                    storage_path,
                )

    return jsonify({"status": "ok", "message_id": msg_id, "tag": tag}), 201


# ── Message retrieval ────────────────────────────────────────────────────────


@bp.route("/messages", methods=["GET"])
@limiter.limit("60 per minute")
@api_key_required
@require_scope("mail:read")
def list_messages():
    user_id = g.user_id
    tag = request.args.get("tag", "")
    q = request.args.get("q", "").strip()

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)

    if per_page > 100:
        per_page = 100

    offset = (page - 1) * per_page

    if q and tag:
        messages = db.search_messages_by_tag(user_id, q, tag, limit=per_page, offset=offset)
        total = db.get_total_search_results_by_tag(user_id, q, tag)
    elif q:
        messages = db.search_messages(user_id, q, limit=per_page, offset=offset)
        total = db.get_total_search_results(user_id, q)
    elif tag:
        messages = db.get_messages_for_user_by_tag(user_id, tag, limit=per_page, offset=offset)
        total = db.get_total_messages_for_user_by_tag(user_id, tag)
    else:
        messages = db.get_messages_for_user(user_id, limit=per_page, offset=offset)
        total = db.get_total_messages_for_user(user_id)

    return jsonify({
        "messages": messages,
        "total": total,
        "page": page,
        "per_page": per_page,
        "tag": tag or None,
        "query": q or None,
    }), 200


@bp.route("/messages/<int:message_id>", methods=["GET"])
@limiter.limit("60 per minute")
@api_key_required
@require_scope("mail:read")
def get_message(message_id):
    user_id = g.user_id

    msg = db.get_message_by_id(message_id)
    if not msg or msg["user_id"] != user_id:
        abort(404)

    attachments = db.get_attachments_for_message(message_id)
    msg["attachments"] = attachments
    return jsonify(msg), 200


# ── Tags ─────────────────────────────────────────────────────────────────────


@bp.route("/tags", methods=["GET"])
@limiter.limit("60 per minute")
@api_key_required
@require_scope("mail:read")
def list_tags():
    tags = db.get_all_tags_for_user(g.user_id)
    return jsonify({"tags": tags}), 200
