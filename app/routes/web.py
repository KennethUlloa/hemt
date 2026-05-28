from flask import Blueprint, render_template, request, abort, send_file, g, flash, redirect, url_for
from markupsafe import Markup
from werkzeug.security import check_password_hash, generate_password_hash

from app.auth.decorators import login_required
from app.auth.helpers import generate_api_key
from app.container import db, storage
from app.database.models import Attachment, Message

bp = Blueprint("web", __name__, url_prefix="")


@bp.route("/docs")
def docs():
    from flask import current_app
    base_url = current_app.config.get("API_BASE_URL", "http://localhost:5000")
    return render_template("docs.html", api_base_url=base_url)


@bp.route("/")
@login_required
def inbox():
    user_id = g.user_id
    tag = request.args.get("tag", "")
    q = request.args.get("q", "").strip()

    page = request.args.get("page", 1, type=int)
    per_page = 25
    offset = (page - 1) * per_page

    if q:
        messages = db.search_messages(user_id, q, limit=per_page, offset=offset)
        total = db.get_total_search_results(user_id, q)
    elif tag:
        messages = db.get_messages_for_user_by_tag(user_id, tag, limit=per_page, offset=offset)
        total = db.get_total_messages_for_user_by_tag(user_id, tag)
    else:
        messages = db.get_messages_for_user(user_id, limit=per_page, offset=offset)
        total = db.get_total_messages_for_user(user_id)

    total_pages = (total + per_page - 1) // per_page
    tags = db.get_all_tags_for_user(user_id)

    return render_template(
        "inbox.html",
        messages=messages,
        page=page,
        total_pages=total_pages,
        tags=tags,
        current_tag=tag,
        query=q,
    )


@bp.route("/message/<int:message_id>")
@login_required
def message_detail(message_id):
    user_id = g.user_id

    msg = db.get_message_by_id(message_id)
    if not msg or msg["user_id"] != user_id:
        abort(404)

    attachments = db.get_attachments_for_message(message_id)
    return render_template("message.html", message=msg, attachments=attachments)


@bp.route("/attachment/<int:attachment_id>")
@login_required
def download_attachment(attachment_id):
    user_id = g.user_id

    att = Attachment.query.get(attachment_id)
    if not att:
        abort(404)

    msg = Message.query.get(att.message_id)
    if not msg or msg.user_id != user_id:
        abort(404)

    file_path = storage.get_path(att.storage_path)
    return send_file(file_path, mimetype=att.content_type, as_attachment=False, download_name=att.filename)


@bp.route("/compose", methods=["GET"])
@login_required
def compose_page():
    return render_template("compose.html")


@bp.route("/compose", methods=["POST"])
@login_required
def compose_action():
    user_id = g.user_id

    from_addr = request.form.get("from_addr", "").strip().lower()
    to_addr = request.form.get("to_addr", "").strip().lower()
    subject = request.form.get("subject", "")
    body_text = request.form.get("body_text", "")
    body_html = request.form.get("body_html", "")

    if not from_addr or not to_addr:
        flash("From and To are required", "error")
        return render_template("compose.html",
                               from_addr=from_addr, to_addr=to_addr,
                               subject=subject, body_text=body_text)

    msg_id = db.create_message(user_id, from_addr, to_addr, subject, body_text, body_html)

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

    flash("Email sent successfully!", "success")
    return redirect(url_for("web.message_detail", message_id=msg_id))


@bp.route("/settings", methods=["GET"])
@login_required
def settings_page():
    user_id = g.user_id
    user = db.get_user_by_id(user_id)
    api_keys = db.get_api_keys_for_user(user_id)
    return render_template("settings.html", user=user, api_keys=api_keys)


@bp.route("/settings/password", methods=["POST"])
@login_required
def settings_change_password():
    user_id = g.user_id
    user = db.get_user_by_id(user_id)

    current = request.form.get("current_password", "")
    new_pass = request.form.get("new_password", "")
    confirm = request.form.get("confirm_password", "")

    if not check_password_hash(user["password_hash"], current):
        flash("Current password is incorrect", "error")
    elif not new_pass or len(new_pass) < 4:
        flash("New password must be at least 4 characters", "error")
    elif new_pass != confirm:
        flash("Passwords do not match", "error")
    else:
        db.update_password(user_id, generate_password_hash(new_pass))
        flash("Password changed successfully", "success")

    return redirect(url_for("web.settings_page"))


@bp.route("/settings/api-keys/create", methods=["POST"])
@login_required
def settings_create_api_key():
    user_id = g.user_id
    name = request.form.get("name", "").strip()
    scopes = ",".join(request.form.getlist("scopes")) or "mail:send,mail:read,keys:manage"
    tag = request.form.get("tag", "").strip()

    if not name:
        flash("API key name is required", "error")
    else:
        full_key, prefix, key_hash = generate_api_key(scopes)
        db.create_api_key(user_id, name, prefix, key_hash, scopes, tag)
        msg = Markup(
            '<strong>API key created!</strong>'
            ' <span class="key-display">'
            f'<code>{full_key}</code>'
            ' <button class="btn btn-sm btn-copy" onclick="copyText(this)">Copy</button>'
            '</span>'
        )
        flash(msg, "success")
    return redirect(url_for("web.settings_page"))


@bp.route("/settings/api-keys/toggle", methods=["POST"])
@login_required
def settings_toggle_api_key():
    user_id = g.user_id
    api_keys = db.get_api_keys_for_user(user_id)

    key_id = request.form.get("key_id", type=int)
    is_active = request.form.get("is_active") == "1"
    if key_id and key_id in [k["id"] for k in api_keys]:
        db.set_api_key_active(key_id, is_active)
        flash("API key updated", "success")
    else:
        flash("API key not found", "error")
    return redirect(url_for("web.settings_page"))


@bp.route("/settings/api-keys/delete", methods=["POST"])
@login_required
def settings_delete_api_key():
    user_id = g.user_id
    api_keys = db.get_api_keys_for_user(user_id)

    key_id = request.form.get("key_id", type=int)
    if key_id and key_id in [k["id"] for k in api_keys]:
        db.delete_api_key(key_id)
        flash("API key deleted", "success")
    else:
        flash("API key not found", "error")
    return redirect(url_for("web.settings_page"))
