from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def _key_func():
    from flask import g, request
    if hasattr(g, "user_id") and g.user_id:
        return f"user_{g.user_id}"
    return get_remote_address()


limiter = Limiter(key_func=_key_func, default_limits=["60 per minute"])
