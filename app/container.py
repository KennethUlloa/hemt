import os
import sys

from app.interfaces.database import DatabaseBackend
from app.interfaces.storage import StorageBackend


def create_database_backend() -> DatabaseBackend:
    backend = os.environ.get("DATABASE_BACKEND", "sqlite").lower()

    if backend == "postgres":
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            print("FATAL: DATABASE_BACKEND=postgres but DATABASE_URL is not set", file=sys.stderr)
            sys.exit(1)
        from app.database.postgres import PostgresBackend
        print(f"* Database: Postgres ({db_url})")
        return PostgresBackend()

    print(f"* Database: SQLite ({os.environ.get('DATABASE_URL', 'default path')})")
    from app.database.sqlite import SQLiteBackend
    return SQLiteBackend()


def create_storage_backend() -> StorageBackend:
    from app.config import Config

    backend = os.environ.get("STORAGE_BACKEND", "local").lower()

    if backend == "s3":
        missing = [v for v in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY") if not os.environ.get(v)]
        if missing:
            print(f"FATAL: STORAGE_BACKEND=s3 but {', '.join(missing)} not set", file=sys.stderr)
            sys.exit(1)
        bucket = os.environ.get("S3_BUCKET_NAME", "emailtrap")
        endpoint = os.environ.get("S3_ENDPOINT_URL", "")
        print(f"* Storage: S3 (bucket={bucket}", end="")
        if endpoint:
            print(f", endpoint={endpoint}", end="")
        print(")")
        from app.storage.s3_storage import S3StorageBackend
        return S3StorageBackend(
            bucket_name=bucket,
            region=os.environ.get("S3_REGION", "us-east-1"),
            prefix=os.environ.get("S3_PREFIX", "attachments"),
            endpoint_url=endpoint,
        )

    print(f"* Storage: Local ({Config.STORAGE_PATH})")
    from app.storage.local_storage import LocalStorageBackend
    return LocalStorageBackend(Config.STORAGE_PATH)


db = create_database_backend()
storage: StorageBackend = None
