from abc import ABC, abstractmethod
from typing import Optional


class DatabaseBackend(ABC):
    @abstractmethod
    def create_user(self, username: str, password_hash: str) -> int:
        ...

    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[dict]:
        ...

    @abstractmethod
    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        ...

    @abstractmethod
    def update_password(self, user_id: int, new_password_hash: str) -> None:
        ...

    @abstractmethod
    def create_message(
        self,
        user_id: int,
        from_addr: str,
        to_addr: str,
        subject: str,
        body_text: str,
        body_html: str,
        tag: str = "",
    ) -> int:
        ...

    @abstractmethod
    def get_message_by_id(self, message_id: int) -> Optional[dict]:
        ...

    @abstractmethod
    def get_messages_for_user(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> list[dict]:
        ...

    @abstractmethod
    def get_messages_for_user_by_tag(
        self, user_id: int, tag: str, limit: int = 50, offset: int = 0
    ) -> list[dict]:
        ...

    @abstractmethod
    def get_total_messages_for_user(self, user_id: int) -> int:
        ...

    @abstractmethod
    def get_total_messages_for_user_by_tag(self, user_id: int, tag: str) -> int:
        ...

    @abstractmethod
    def create_attachment(
        self, message_id: int, filename: str, content_type: str, size: int, storage_path: str
    ) -> int:
        ...

    @abstractmethod
    def get_attachments_for_message(self, message_id: int) -> list[dict]:
        ...

    @abstractmethod
    def create_api_key(
        self, user_id: int, name: str, prefix: str, key_hash: str,
        scopes: str = "", tag: str = "",
    ) -> int:
        ...

    @abstractmethod
    def get_api_key_by_prefix(self, prefix: str) -> Optional[dict]:
        ...

    @abstractmethod
    def get_api_keys_for_user(self, user_id: int) -> list[dict]:
        ...

    @abstractmethod
    def revoke_api_key(self, key_id: int) -> bool:
        ...

    @abstractmethod
    def set_api_key_active(self, key_id: int, is_active: bool) -> bool:
        ...

    @abstractmethod
    def delete_api_key(self, key_id: int) -> bool:
        ...

    @abstractmethod
    def update_api_key_used(self, key_id: int) -> None:
        ...

    @abstractmethod
    def create_session(self, session_id: str, user_id: int, data: str, expires_at: str) -> None:
        ...

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[dict]:
        ...

    @abstractmethod
    def update_session_data(self, session_id: str, data: str) -> None:
        ...

    @abstractmethod
    def delete_session(self, session_id: str) -> None:
        ...

    @abstractmethod
    def cleanup_expired_sessions(self) -> None:
        ...

    @abstractmethod
    def get_all_tags_for_user(self, user_id: int) -> list[str]:
        ...

    @abstractmethod
    def search_messages(
        self, user_id: int, query: str, limit: int = 50, offset: int = 0
    ) -> list[dict]:
        ...

    @abstractmethod
    def get_total_search_results(self, user_id: int, query: str) -> int:
        ...
