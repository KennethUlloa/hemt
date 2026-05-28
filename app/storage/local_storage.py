import os
import uuid
from typing import BinaryIO

from werkzeug.utils import secure_filename

from app.interfaces.storage import StorageBackend


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_path: str):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def save(self, filename: str, content: BinaryIO) -> str:
        safe_name = secure_filename(filename)
        unique_id = uuid.uuid4().hex
        storage_path = os.path.join(unique_id[:2], unique_id[2:4], f"{unique_id}_{safe_name}")

        full_path = os.path.join(self.base_path, storage_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        content.save(full_path)
        return storage_path

    def get_path(self, storage_path: str) -> str:
        return os.path.join(self.base_path, storage_path)
