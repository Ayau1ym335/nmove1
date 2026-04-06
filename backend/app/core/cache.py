import logging
import json
from functools import wraps
from typing import Any, Callable
from app.core.redis import redis_client

logger = logging.getLogger("nmove.cache")

DEFAULT_TTL = 300  # 5 minutes

async def cache_get(key: str) -> Any | None:
    try:
        raw = await redis_client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"Cache GET failed for key={key}: {e}")
        return None

async def cache_set(key: str, value: Any, ttl: int = DEFAULT_TTL) -> bool:
    try:
        serialized = json.dumps(value, default=str)
        await redis_client.set(key, serialized, ex=ttl)
        return True
    except Exception as e:
        logger.warning(f"Cache SET failed for key={key}: {e}")
        return False

async def cache_delete(key: str) -> bool:
    try:
        await redis_client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache DELETE failed for key={key}: {e}")
        return False

async def cache_delete_pattern(pattern: str) -> int:
    try:
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)
        return len(keys)
    except Exception as e:
        logger.warning(f"Cache DELETE pattern failed for {pattern}: {e}")
        return 0

def dashboard_cache_key(user_id: str) -> str:
    return f"dashboard:summary:{user_id}"

def session_cache_key(session_id: str) -> str:
    return f"session:detail:{session_id}"

async def invalidate_user_dashboard(user_id: str) -> None:
    key = dashboard_cache_key(str(user_id))
    deleted = await cache_delete(key)
    logger.info(f"Dashboard cache invalidated for user={user_id}: {deleted}")
