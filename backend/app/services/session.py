import json
import secrets
from typing import Any

import redis.asyncio as redis

from app.config import settings

_redis: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


def _key(session_id: str) -> str:
    return f"encore:session:{session_id}"


async def create_session() -> str:
    session_id = secrets.token_urlsafe(32)
    r = await get_redis()
    await r.set(
        _key(session_id),
        json.dumps({}),
        ex=settings.session_ttl_seconds,
    )
    return session_id


async def get_session(session_id: str) -> dict[str, Any] | None:
    r = await get_redis()
    raw = await r.get(_key(session_id))
    if raw is None:
        return None
    return json.loads(raw)


async def update_session(session_id: str, data: dict[str, Any]) -> None:
    r = await get_redis()
    existing = await get_session(session_id)
    if existing is None:
        existing = {}
    existing.update(data)
    await r.set(
        _key(session_id),
        json.dumps(existing),
        ex=settings.session_ttl_seconds,
    )


async def delete_session(session_id: str) -> None:
    r = await get_redis()
    await r.delete(_key(session_id))
