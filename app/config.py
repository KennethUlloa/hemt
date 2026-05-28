import os
from dotenv import load_dotenv

load_dotenv()

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(_project_root, "instance", "emailtrap.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local")
    STORAGE_PATH = os.path.abspath(os.environ.get("STORAGE_PATH", os.path.join(_project_root, "attachments")))

    API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:5000")

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB max upload
