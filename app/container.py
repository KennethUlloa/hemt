import os

from app.interfaces.database import DatabaseBackend
from app.interfaces.storage import StorageBackend


def create_database_backend() -> DatabaseBackend:
    backend = os.environ.get("DATABASE_BACKEND", "sqlite").lower()

    if backend == "postgres":
        from app.database.postgres import PostgresBackend
        return PostgresBackend()

    from app.database.sqlite import SQLiteBackend
    return SQLiteBackend()


def create_storage_backend() -> StorageBackend:
    from app.config import Config

    backend = os.environ.get("STORAGE_BACKEND", "local").lower()

    if backend == "s3":
        from app.storage.s3_storage import S3StorageBackend
        return S3StorageBackend(
            bucket_name=os.environ.get("S3_BUCKET_NAME", "emailtrap"),
            region=os.environ.get("S3_REGION", "us-east-1"),
            prefix=os.environ.get("S3_PREFIX", "attachments"),
            endpoint_url=os.environ.get("S3_ENDPOINT_URL", ""),
        )

    from app.storage.local_storage import LocalStorageBackend
    return LocalStorageBackend(Config.STORAGE_PATH)


db = create_database_backend()
storage: StorageBackend = None
