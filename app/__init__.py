import os

from flask import Flask, g, request
from sqlalchemy import inspect, text

from app.config import Config
from app.database.models import db as sqla_db
from app.container import db
from app import container


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(os.path.join(os.getcwd(), "instance"), exist_ok=True)

    sqla_db.init_app(app)

    container.storage = container.create_storage_backend()

    from app.routes import auth, web, api
    app.register_blueprint(auth.bp)
    app.register_blueprint(web.bp)
    app.register_blueprint(api.bp)

    @app.get("/health")
    def health():
        return "OK", 200

    from app.limiter import limiter
    limiter.init_app(app)

    @app.before_request
    def load_session_user():
        from app.auth.helpers import get_session_data
        session_id = request.cookies.get("sid")
        if session_id:
            data = get_session_data(session_id)
            if data and "user_id" in data:
                g.user_id = data["user_id"]
                user = db.get_user_by_id(data["user_id"])
                g.username = user["username"] if user else None
            else:
                g.user_id = None
                g.username = None
        else:
            g.user_id = None
            g.username = None

    with app.app_context():
        sqla_db.create_all()
        _run_migrations()

    return app


def _run_migrations():
    engine = sqla_db.engine
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    with engine.begin() as conn:
        if "api_keys" in tables:
            cols = [c["name"] for c in inspector.get_columns("api_keys")]
            if "scopes" not in cols:
                conn.execute(text(
                    "ALTER TABLE api_keys ADD COLUMN scopes TEXT DEFAULT 'mail:send,mail:read,keys:manage'"
                ))
            if "tag" not in cols:
                conn.execute(text(
                    "ALTER TABLE api_keys ADD COLUMN tag TEXT DEFAULT ''"
                ))

        if "messages" in tables:
            cols = [c["name"] for c in inspector.get_columns("messages")]
            if "user_id" not in cols:
                conn.execute(text("ALTER TABLE messages ADD COLUMN user_id INTEGER REFERENCES users(id)"))
            if "tag" not in cols:
                conn.execute(text("ALTER TABLE messages ADD COLUMN tag TEXT DEFAULT ''"))
            if "account_id" in cols:
                conn.execute(text("DROP INDEX IF EXISTS ix_messages_account_id"))

    if "sessions" not in tables:
        from app.database.models import Session
        sqla_db.create_all()
