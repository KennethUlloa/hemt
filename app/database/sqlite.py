import json
from typing import Optional
from datetime import datetime

from app.interfaces.database import DatabaseBackend
from app.database.models import (
    db, User, Message, Attachment, ApiKey, Session,
)


class SQLiteBackend(DatabaseBackend):
    def create_user(self, username: str, password_hash: str) -> int:
        user = User(username=username, password_hash=password_hash)
        db.session.add(user)
        db.session.commit()
        return user.id

    def get_user_by_username(self, username: str) -> Optional[dict]:
        user = User.query.filter_by(username=username).first()
        if not user:
            return None
        return {"id": user.id, "username": user.username, "password_hash": user.password_hash, "is_active": user.is_active}

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        user = User.query.get(user_id)
        if not user:
            return None
        return {"id": user.id, "username": user.username, "password_hash": user.password_hash, "is_active": user.is_active}

    def update_password(self, user_id: int, new_password_hash: str) -> None:
        User.query.filter_by(id=user_id).update({"password_hash": new_password_hash})
        db.session.commit()

    def set_user_active(self, user_id: int, is_active: bool) -> bool:
        user = User.query.get(user_id)
        if not user:
            return False
        user.is_active = is_active
        db.session.commit()
        return True

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
        msg = Message(
            user_id=user_id,
            from_addr=from_addr,
            to_addr=to_addr,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            tag=tag,
        )
        db.session.add(msg)
        db.session.commit()
        return msg.id

    def get_message_by_id(self, message_id: int) -> Optional[dict]:
        msg = Message.query.get(message_id)
        if not msg:
            return None
        return self._message_to_dict(msg)

    def get_messages_for_user(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> list[dict]:
        msgs = (
            Message.query.filter_by(user_id=user_id)
            .order_by(Message.received_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [self._message_to_dict(m) for m in msgs]

    def get_messages_for_user_by_tag(
        self, user_id: int, tag: str, limit: int = 50, offset: int = 0
    ) -> list[dict]:
        msgs = (
            Message.query.filter_by(user_id=user_id, tag=tag)
            .order_by(Message.received_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [self._message_to_dict(m) for m in msgs]

    def get_total_messages_for_user(self, user_id: int) -> int:
        return Message.query.filter_by(user_id=user_id).count()

    def get_total_messages_for_user_by_tag(self, user_id: int, tag: str) -> int:
        return Message.query.filter_by(user_id=user_id, tag=tag).count()

    def create_attachment(
        self, message_id: int, filename: str, content_type: str, size: int, storage_path: str
    ) -> int:
        att = Attachment(
            message_id=message_id,
            filename=filename,
            content_type=content_type,
            size=size,
            storage_path=storage_path,
        )
        db.session.add(att)
        db.session.commit()
        return att.id

    def get_attachments_for_message(self, message_id: int) -> list[dict]:
        atts = Attachment.query.filter_by(message_id=message_id).all()
        return [
            {
                "id": a.id,
                "message_id": a.message_id,
                "filename": a.filename,
                "content_type": a.content_type,
                "size": a.size,
                "storage_path": a.storage_path,
            }
            for a in atts
        ]

    def create_api_key(self, user_id: int, name: str, prefix: str, key_hash: str, scopes: str = "", tag: str = "") -> int:
        key = ApiKey(
            user_id=user_id, name=name, prefix=prefix,
            key_hash=key_hash,
            scopes=scopes or "mail:send,mail:read,keys:manage",
            tag=tag,
        )
        db.session.add(key)
        db.session.commit()
        return key.id

    def get_api_key_by_prefix(self, prefix: str) -> Optional[dict]:
        key = ApiKey.query.filter_by(prefix=prefix, is_active=True).first()
        if not key:
            return None
        return {
            "id": key.id,
            "user_id": key.user_id,
            "name": key.name,
            "prefix": key.prefix,
            "key_hash": key.key_hash,
            "scopes": key.scopes,
            "tag": key.tag,
            "is_active": key.is_active,
        }

    def get_api_keys_for_user(self, user_id: int) -> list[dict]:
        keys = ApiKey.query.filter_by(user_id=user_id).order_by(ApiKey.created_at.desc()).all()
        return [
            {
                "id": k.id,
                "name": k.name,
                "prefix": k.prefix,
                "scopes": k.scopes,
                "tag": k.tag,
                "is_active": k.is_active,
                "created_at": k.created_at.isoformat() if k.created_at else None,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            }
            for k in keys
        ]

    def revoke_api_key(self, key_id: int) -> bool:
        return self.set_api_key_active(key_id, False)

    def set_api_key_active(self, key_id: int, is_active: bool) -> bool:
        key = ApiKey.query.get(key_id)
        if not key:
            return False
        key.is_active = is_active
        db.session.commit()
        return True

    def delete_api_key(self, key_id: int) -> bool:
        key = ApiKey.query.get(key_id)
        if not key:
            return False
        db.session.delete(key)
        db.session.commit()
        return True

    def update_api_key_used(self, key_id: int) -> None:
        ApiKey.query.filter_by(id=key_id).update({"last_used_at": datetime.utcnow()})
        db.session.commit()

    def create_session(self, session_id: str, user_id: int, data: str, expires_at: str) -> None:
        sess = Session(
            session_id=session_id,
            user_id=user_id,
            data=data,
            expires_at=datetime.fromisoformat(expires_at),
        )
        db.session.add(sess)
        db.session.commit()

    def get_session(self, session_id: str) -> Optional[dict]:
        sess = Session.query.filter_by(session_id=session_id).first()
        if not sess:
            return None
        if sess.expires_at < datetime.utcnow():
            db.session.delete(sess)
            db.session.commit()
            return None
        return {
            "id": sess.id,
            "session_id": sess.session_id,
            "user_id": sess.user_id,
            "data": sess.data,
            "expires_at": sess.expires_at.isoformat(),
        }

    def update_session_data(self, session_id: str, data: str) -> None:
        Session.query.filter_by(session_id=session_id).update({"data": data})
        db.session.commit()

    def delete_session(self, session_id: str) -> None:
        Session.query.filter_by(session_id=session_id).delete()
        db.session.commit()

    def cleanup_expired_sessions(self) -> None:
        Session.query.filter(Session.expires_at < datetime.utcnow()).delete()
        db.session.commit()

    def get_all_tags_for_user(self, user_id: int) -> list[str]:
        rows = (
            db.session.query(Message.tag)
            .filter(Message.user_id == user_id, Message.tag != "")
            .distinct()
            .all()
        )
        return [r[0] for r in rows]

    def search_messages(
        self, user_id: int, query: str, limit: int = 50, offset: int = 0
    ) -> list[dict]:
        pattern = f"%{query}%"
        msgs = (
            Message.query.filter(
                Message.user_id == user_id,
                db.or_(
                    Message.subject.ilike(pattern),
                    Message.to_addr.ilike(pattern),
                    Message.from_addr.ilike(pattern),
                    Message.tag.ilike(pattern),
                ),
            )
            .order_by(Message.received_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [self._message_to_dict(m) for m in msgs]

    def get_total_search_results(self, user_id: int, query: str) -> int:
        pattern = f"%{query}%"
        return Message.query.filter(
            Message.user_id == user_id,
            db.or_(
                Message.subject.ilike(pattern),
                Message.to_addr.ilike(pattern),
                Message.from_addr.ilike(pattern),
                Message.tag.ilike(pattern),
            ),
        ).count()

    def search_messages_by_tag(
        self, user_id: int, query: str, tag: str, limit: int = 50, offset: int = 0
    ) -> list[dict]:
        pattern = f"%{query}%"
        msgs = (
            Message.query.filter(
                Message.user_id == user_id,
                Message.tag == tag,
                db.or_(
                    Message.subject.ilike(pattern),
                    Message.to_addr.ilike(pattern),
                    Message.from_addr.ilike(pattern),
                    Message.tag.ilike(pattern),
                ),
            )
            .order_by(Message.received_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [self._message_to_dict(m) for m in msgs]

    def get_total_search_results_by_tag(self, user_id: int, query: str, tag: str) -> int:
        pattern = f"%{query}%"
        return Message.query.filter(
            Message.user_id == user_id,
            Message.tag == tag,
            db.or_(
                Message.subject.ilike(pattern),
                Message.to_addr.ilike(pattern),
                Message.from_addr.ilike(pattern),
                Message.tag.ilike(pattern),
            ),
        ).count()

    def _message_to_dict(self, msg: Message) -> dict:
        return {
            "id": msg.id,
            "user_id": msg.user_id,
            "from_addr": msg.from_addr,
            "to_addr": msg.to_addr,
            "subject": msg.subject,
            "body_text": msg.body_text,
            "body_html": msg.body_html,
            "tag": msg.tag,
            "received_at": msg.received_at.isoformat() if msg.received_at else None,
        }
