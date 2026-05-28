from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    messages = db.relationship("Message", back_populates="user", cascade="all, delete-orphan")
    sessions = db.relationship("Session", back_populates="user", cascade="all, delete-orphan")


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    from_addr = db.Column(db.String(254), nullable=False)
    to_addr = db.Column(db.String(254), nullable=False)
    subject = db.Column(db.String(998), default="")
    body_text = db.Column(db.Text, default="")
    body_html = db.Column(db.Text, default="")
    tag = db.Column(db.String(120), default="")
    received_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship("User", back_populates="messages")
    attachments = db.relationship("Attachment", back_populates="message", cascade="all, delete-orphan")


class Attachment(db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey("messages.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(255), default="application/octet-stream")
    size = db.Column(db.Integer, default=0)
    storage_path = db.Column(db.String(512), nullable=False)

    message = db.relationship("Message", back_populates="attachments")


class ApiKey(db.Model):
    __tablename__ = "api_keys"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    prefix = db.Column(db.String(8), nullable=False, unique=True, index=True)
    key_hash = db.Column(db.String(256), nullable=False)
    scopes = db.Column(db.Text, default="mail:send,mail:read,accounts:manage,keys:manage")
    tag = db.Column(db.String(120), default="")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    last_used_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User")


class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    data = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    user = db.relationship("User", back_populates="sessions")
