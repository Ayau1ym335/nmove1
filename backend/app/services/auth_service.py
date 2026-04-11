"""app/services/auth_service.py — Business logic for registration, login,
token refresh, and logout.

This module contains no route logic. All DB operations are async.
"""
import hashlib
import logging
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import delete_refresh_token, get_refresh_token_user_id, store_refresh_token
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    verify_password,
)
from app.models.session import AuthSession
from app.models.user import User
from app.models.profile import Profile
from app.schemas.auth import (
    LoginRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserOut,
)

logger = logging.getLogger(__name__)

# A dummy hash used to prevent timing attacks when the user is not found.
# verify_password is called unconditionally so response time is the same
# whether the email exists or not.
_DUMMY_HASH = hash_password("dummy_timing_guard_password_that_never_matches")


async def register_user(db: AsyncSession, data: RegisterRequest) -> RegisterResponse:
    """Create a new user account.

    Steps:
    1. Check for duplicate email (HTTP 409 if taken).
    2. Hash password immediately — plain text is never persisted.
    3. Persist the User row and return a RegisterResponse.

    Args:
        db:   Async SQLAlchemy session.
        data: Validated registration payload.

    Returns:
        RegisterResponse containing the created UserOut and a success message.

    Raises:
        HTTPException 409: If the email is already registered.
    """
    # 1. Duplicate-email guard
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )

    # 2. Hash password — plaintext never leaves this scope
    hashed = hash_password(data.password)

    # 3. Persist
    user = User(
        email=data.email,
        hashed_password=hashed,
        role=data.role,
        full_name=data.full_name,
        is_active=True,
    )
    db.add(user)

    if data.role == "patient" and data.profile is not None:
        # Fail fast with a clear message if DB schema is behind code.
        # This prevents opaque "relation does not exist" runtime errors.
        profiles_table_exists = await db.scalar(
            text("SELECT to_regclass('public.profiles')")
        )
        if profiles_table_exists is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Registration is temporarily unavailable: profiles schema is missing. "
                    "Run database migrations (alembic upgrade head)."
                ),
            )

        profile = Profile(
            user=user,
            age=data.profile.age,
            gender=data.profile.gender,
            weight=data.profile.weight,
            height=data.profile.height,
            nationality=data.profile.nationality,
            have_injury=data.profile.have_injury,
            have_banomaly=data.profile.have_banomaly,
            banomaly=data.profile.banomaly,
            shoe_size=data.profile.shoe_size,
            leg_length=data.profile.leg_length,
            dominant_leg=data.profile.dominant_leg,
            lifestyle=data.profile.lifestyle,
            smoke=data.profile.smoke,
            alcohol=data.profile.alcohol,
            notes=data.profile.notes,
        )
        db.add(profile)

    await db.commit()
    await db.refresh(user)

    return RegisterResponse(user=UserOut.model_validate(user))


async def login_user(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    """Authenticate with email + password, issue access + refresh tokens.

    Steps:
    1. Fetch user by email.
    2. Verify password — identical error for wrong email and wrong password
       to prevent user enumeration attacks. verify_password() is ALWAYS called
       (even when user is None) to prevent timing-based email enumeration.
    3. Check is_active (403 not 401 — user is known, just disabled).
    4. Create JWT access token.
    5. Generate opaque refresh token; store hash in DB + Redis.
    6. Return TokenResponse.

    Args:
        db:   Async SQLAlchemy session.
        data: Validated login payload.

    Returns:
        TokenResponse with access_token, refresh_token, and expires_in.

    Raises:
        HTTPException 401: On invalid credentials (same message either case).
        HTTPException 403: If account is disabled.
    """
    # 1. Fetch user
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    # 2. Validate credentials — ALWAYS call verify_password to prevent timing
    #    attacks that distinguish "email not found" from "wrong password".
    #    If user is None, compare against a pre-computed dummy hash so the
    #    bcrypt work factor is always exercised.
    stored_hash = user.hashed_password if user is not None else _DUMMY_HASH
    password_ok = verify_password(data.password, stored_hash)

    if user is None or not password_ok:
        # Identical message regardless of whether email or password was wrong.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Active-account check (after password verify — same timing)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled.",
        )

    # 4. JWT access token
    access_token = create_access_token(user.id, user.role.value)

    # 5. Opaque refresh token — only hash is persisted; raw token goes to client
    raw_token, token_hash = generate_refresh_token()

    expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    auth_session = AuthSession(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(auth_session)
    await db.commit()

    # 6. Cache hash in Redis for fast-path refresh/logout lookups
    await store_refresh_token(token_hash, user.id, settings.REFRESH_TOKEN_EXPIRE_DAYS)

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def refresh_tokens(db: AsyncSession, raw_refresh_token: str) -> RefreshResponse:
    """Exchange a valid refresh token for a new rotated access + refresh token pair.

    Full token rotation: old token is invalidated (DB + Redis) and a brand-new
    pair is issued. If any step in the rotation fails, everything is rolled back.

    Steps:
    1. Compute SHA-256 hash of raw token (never store/log the raw value).
    2. Fast-path lookup in Redis — 401 if missing.
    3. Validate the DB session row and check expiry.
    4. Load and verify the user is active.
    5. Atomically rotate: delete old entries, create new ones.
    6. Return RefreshResponse with new token pair.

    Args:
        db:               Async SQLAlchemy session.
        raw_refresh_token: Raw (un-hashed) refresh token from the client.

    Returns:
        RefreshResponse with new access_token, refresh_token, and expires_in.

    Raises:
        HTTPException 401: On invalid, expired, or missing refresh token.
        HTTPException 500: If token rotation fails midway.
    """
    # 1. Compute hash — raw token is never logged or stored
    token_hash = hashlib.sha256(raw_refresh_token.encode()).hexdigest()

    # 2. Fast-path: check Redis first (cheap O(1) lookup)
    user_id_str = await get_refresh_token_user_id(token_hash)
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Validate DB session row exists and is not expired
    result = await db.execute(
        select(AuthSession).where(AuthSession.token_hash == token_hash)
    )
    session = result.scalar_one_or_none()
    if session is None:
        # Redis has it but DB doesn't — clean up the Redis orphan
        await delete_refresh_token(token_hash)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    now = datetime.now(UTC)
    exp = session.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=UTC)
    if exp < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Load user and verify active
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id_str)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 5. TOKEN ROTATION — full rollback if any step fails
    new_hash: str | None = None
    new_raw: str | None = None
    try:
        # 5a. Delete old session row from DB
        await db.delete(session)

        # 5b. Delete old key from Redis (before generating new ones)
        await delete_refresh_token(token_hash)

        # 5c. Generate new cryptographically-secure token pair
        new_raw, new_hash = generate_refresh_token()

        # 5d. Insert new AuthSession row
        new_expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        new_session = AuthSession(
            user_id=user.id,
            token_hash=new_hash,
            expires_at=new_expires_at,
        )
        db.add(new_session)

        # 5e. Commit DB atomically (old deleted + new inserted in one transaction)
        await db.commit()

        # 5f. Store new hash in Redis (after successful DB commit)
        await store_refresh_token(new_hash, user.id, settings.REFRESH_TOKEN_EXPIRE_DAYS)

    except Exception:
        logger.exception(
            "Token rotation failed for user_id=%s — rolling back", user_id_str
        )
        await db.rollback()
        # Clean up new Redis key if it was stored before the failure
        if new_hash is not None:
            await delete_refresh_token(new_hash)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token rotation failed",
        )

    # 6. Create new access token (after successful rotation)
    new_access_token = create_access_token(user.id, user.role.value)

    # Log user_id only — raw token and hash are never logged
    logger.info("Tokens refreshed for user_id=%s", user.id)

    # 7. Return new token pair
    return RefreshResponse(
        access_token=new_access_token,
        refresh_token=new_raw,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def logout_user(db: AsyncSession, raw_refresh_token: str) -> dict:
    """Revoke a refresh token — idempotent, always returns success.

    Steps:
    1. Compute SHA-256 hash of raw token.
    2. Delete from Redis (idempotent — no error if key absent).
    3. Delete from DB (idempotent — no error if row absent).
    4. Commit DB.
    5. Return success message.

    Args:
        db:               Async SQLAlchemy session.
        raw_refresh_token: Raw refresh token from the client.

    Returns:
        dict with "message" key confirming logout.
    """
    # 1. Compute hash — raw token is never logged
    token_hash = hashlib.sha256(raw_refresh_token.encode()).hexdigest()

    # 2. Delete from Redis (no-op if key is already gone)
    await delete_refresh_token(token_hash)

    # 3. Delete from DB using bulk DELETE — no-op if row absent
    await db.execute(
        delete(AuthSession).where(AuthSession.token_hash == token_hash)
    )

    # 4. Commit
    await db.commit()

    # 5. Always return success (idempotent)
    return {"message": "Logged out successfully"}
