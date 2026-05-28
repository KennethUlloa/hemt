from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from werkzeug.security import check_password_hash, generate_password_hash

from app.container import db
from app.auth.helpers import create_session, destroy_session

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


@bp.route("/login", methods=["POST"])
def login_action():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    user = db.get_user_by_username(username)
    if not user or not check_password_hash(user["password_hash"], password):
        flash("Invalid username or password", "error")
        return render_template("login.html")

    session_id = create_session(user["id"])
    resp = make_response(redirect(url_for("web.inbox")))
    resp.set_cookie("sid", session_id, max_age=7 * 86400, httponly=True, samesite="Lax")
    return resp


@bp.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")


@bp.route("/register", methods=["POST"])
def register_action():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if not username or not password:
        flash("Username and password are required", "error")
        return render_template("register.html")

    existing = db.get_user_by_username(username)
    if existing:
        flash("Username already exists", "error")
        return render_template("register.html")

    user_id = db.create_user(username, generate_password_hash(password))

    session_id = create_session(user_id)
    resp = make_response(redirect(url_for("web.inbox")))
    resp.set_cookie("sid", session_id, max_age=7 * 86400, httponly=True, samesite="Lax")
    return resp


@bp.route("/logout")
def logout():
    session_id = request.cookies.get("sid")
    if session_id:
        destroy_session(session_id)
    resp = make_response(redirect(url_for("auth.login_page")))
    resp.set_cookie("sid", "", max_age=0)
    return resp
