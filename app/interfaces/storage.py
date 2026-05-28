from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageBackend(ABC):
    @abstractmethod
    def save(self, filename: str, content: BinaryIO) -> str:
        ...

    @abstractmethod
    def get_path(self, storage_path: str) -> str:
        ...
