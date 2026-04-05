"""app/core/dependencies.py — FastAPI reusable dependencies.

# Usage guide:
# Any authenticated user:   current_user: User = Depends(require_any_role)
# Patient only:             current_user: User = Depends(require_patient)
# Doctor only:              current_user: User = Depends(require_doctor)
# Raw user object:          current_user: User = Depends(get_current_user)

Provides:
  - get_redis             — shared aioredis client from core.redis
  - get_token_from_header — extract raw Bearer token from Authorization header
  - get_current_user      — decode JWT, load User from DB (no Redis hit)
  - require_patient       — asserts current user has role=patient (403 otherwise)
  - require_doctor        — asserts current user has role=doctor  (403 otherwise)
  - require_any_role      — named function; any authenticated user passes
"""
import logging
import uuid

import redis.asyncio as aioredis
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import redis_client  # shared singleton
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Redis dependency
# ---------------------------------------------------------------------------


async def get_redis() -> aioredis.Redis:
    """Return the shared async Redis client."""
    return redis_client


# ---------------------------------------------------------------------------
# Token extraction (sync — no I/O)
# ---------------------------------------------------------------------------


def get_token_from_header(authorization: str | None = Header(None)) -> str:
    """Extract the raw Bearer token from the Authorization header.

    This is a synchronous dependency (no I/O) — FastAPI handles it correctly.

    Raises:
        HTTPException 401: If the header is missing or does not start with
        "Bearer " (note the trailing space).
    """
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return authorization[len("Bearer "):]


# ---------------------------------------------------------------------------
# JWT dependency — primary auth guard
# ---------------------------------------------------------------------------


async def get_current_user(
    token: str = Depends(get_token_from_header),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode the Bearer JWT and return the corresponding User ORM object.

    - Calls decode_access_token() which raises HTTP 401 internally on
      expired / tampered / invalid tokens.
    - Validates user exists in DB and is active.
    - Does NOT hit Redis — the JWT is self-contained for reads.

    Raises:
        HTTPException 401: If token is invalid/expired, or user does not exist.
        HTTPException 403: If user account is disabled.
    """
    # decode_access_token raises HTTP 401 internally on any JWT error,
    # including checking the token type claim ("type": "access")
    payload = decode_access_token(token)

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Parse the UUID — invalid UUID string raises ValueError → 401
    try:
        parsed_user_id = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == parsed_user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    return user


# ---------------------------------------------------------------------------
# Role-gated dependencies
# ---------------------------------------------------------------------------


async def require_patient(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require role == patient; raises HTTP 403 (not 401) otherwise.

    The user IS authenticated — the wrong role is an authorization failure,
    not an authentication failure. 403 is the correct status code.
    Logs a warning including user_id and actual role on failure.
    """
    if current_user.role != UserRole.patient:
        logger.warning(
            "Role guard failed: user=%s role=%s required=patient",
            current_user.id,
            current_user.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient access required",
        )
    return current_user


async def require_doctor(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require role == doctor; raises HTTP 403 (not 401) otherwise.

    The user IS authenticated — the wrong role is an authorization failure,
    not an authentication failure. 403 is the correct status code.
    Logs a warning including user_id and actual role on failure.
    """
    if current_user.role != UserRole.doctor:
        logger.warning(
            "Role guard failed: user=%s role=%s required=doctor",
            current_user.id,
            current_user.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor access required",
        )
    return current_user


async def require_any_role(
    current_user: User = Depends(get_current_user),
) -> User:
    """Any authenticated user passes — no role restriction.

    This is a *named* function (not just an alias assignment) so that:
    1. FastAPI's dependency graph treats it as a distinct node.
    2. Route signatures make the intent explicit: "any logged-in user".
    """
    return current_user
