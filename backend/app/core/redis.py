"""app/core/redis.py — Async Redis client singleton and refresh-token helpers."""
import logging
import uuid

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Client singleton — created once at module load, reused across all requests.
# ---------------------------------------------------------------------------

redis_client: aioredis.Redis = aioredis.from_url(
    settings.REDIS_URL,
    decode_responses=True,   # all values are returned as str, never bytes
)


async def get_redis() -> aioredis.Redis:
    """Return the shared async Redis client."""
    return redis_client


# ---------------------------------------------------------------------------
# Refresh-token helpers
# Key format: "refresh:{token_hash}" → str(user_id), TTL = expire_days * 86400 s
# ---------------------------------------------------------------------------

_KEY_PREFIX = "refresh"


async def store_refresh_token(
    token_hash: str,
    user_id: uuid.UUID | str,
    expire_days: int = settings.REFRESH_TOKEN_EXPIRE_DAYS,
) -> None:
    """Persist a refresh-token hash → user_id mapping with a TTL.

    Only the SHA-256 hash of the raw token is stored. The raw token is
    never stored server-side.

    Args:
        token_hash:  SHA-256 hex digest of the raw refresh token.
        user_id:     Owner of the token.
        expire_days: TTL in days (converted to seconds internally).
    """
    ttl_seconds = expire_days * 86_400
    await redis_client.set(
        f"{_KEY_PREFIX}:{token_hash}",
        str(user_id),
        ex=ttl_seconds,      # EX sets the TTL in seconds
    )


async def delete_refresh_token(token_hash: str) -> None:
    """Remove a refresh-token entry from Redis.

    Silently succeeds if the key does not exist (idempotent).

    Args:
        token_hash: SHA-256 hex digest of the raw refresh token.
    """
    await redis_client.delete(f"{_KEY_PREFIX}:{token_hash}")


async def get_refresh_token_user_id(token_hash: str) -> str | None:
    """Look up the user_id associated with a refresh-token hash.

    Args:
        token_hash: SHA-256 hex digest of the raw refresh token.

    Returns:
        The user_id string if the key exists and has not expired, else None.
    """
    return await redis_client.get(f"{_KEY_PREFIX}:{token_hash}")
