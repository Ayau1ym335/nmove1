"""app/routers/auth.py — Authentication endpoints.

Routes:
    POST /auth/register — create account (201)
    POST /auth/login    — authenticate, receive JWT + refresh token (200)
    GET  /auth/me       — return current user (JWT-protected, any role) (200)
    POST /auth/refresh  — rotate refresh token (no auth header needed) (200)
    POST /auth/logout   — revoke refresh token (must be logged in) (200)
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_any_role, require_patient
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserOut,
)
from app.services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    """Create a new user account.

    - Hashes the password with bcrypt before persisting.
    - Returns user info wrapped in RegisterResponse (no password fields).
    - Returns 409 if email already exists.
    """
    try:
        response = await auth_service.register_user(db, body)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error during registration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    # Log user_id and role only — never log email or password
    logger.info("New user registered: user_id=%s role=%s", response.user.id, response.user.role)
    return response


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login and receive access + refresh tokens",
)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate with email + password.

    On success returns:
    - ``access_token`` — signed JWT, expires in ACCESS_TOKEN_EXPIRE_MINUTES.
    - ``refresh_token`` — opaque token; only its SHA-256 hash is stored.
    - ``expires_in``   — seconds until the access token expires.
    """
    try:
        token_response = await auth_service.login_user(db, body)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error during login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    # Log event only — never log email, password, or token values
    logger.info("User login successful")
    return token_response


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    summary="Return the currently authenticated user",
)
async def get_me(
    current_user: User = Depends(require_any_role),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """Protected route — requires a valid Bearer JWT (any authenticated role).

    Returns the UserOut schema for the current user.
    Identity comes from the Authorization header — no request body needed.
    """
    try:
        return UserOut.model_validate(current_user)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error in GET /auth/me")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh token and issue a new access token",
)
async def refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> RefreshResponse:
    """Exchange a valid refresh token for a new rotated access + refresh token pair.

    No Authorization header is required — the refresh token IS the credential.
    Old token is deleted from Redis + DB (strict rotation policy).
    Token values are never logged — only user_id appears in logs.
    """
    try:
        result = await auth_service.refresh_tokens(db, body.refresh_token)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error during token refresh")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    logger.info("Token refresh completed")
    return result


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Invalidate the current refresh token",
)
async def logout(
    body: LogoutRequest,
    current_user: User = Depends(require_any_role),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Revoke the supplied refresh token.

    Requires a valid Bearer JWT to prevent anonymous token-stuffing.
    Idempotent — calling twice both return 200 with the same message.
    """
    try:
        return await auth_service.logout_user(db, body.refresh_token)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error during logout")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# ---------------------------------------------------------------------------
# GET /auth/patient-only-test  — Day 1 role guard smoke-test stub
# ---------------------------------------------------------------------------


@router.get(
    "/patient-only-test",
    status_code=status.HTTP_200_OK,
    summary="Patient-only test route for role guard verification",
    include_in_schema=True,
    tags=["auth"],
)
async def patient_only_test(
    current_user: User = Depends(require_patient),
) -> dict:
    """Stub route protected by patient role check.

    Used by Postman role guard test #8 to verify that a doctor token receives
    HTTP 403 on a patient-only endpoint. Returns 200 for patients, 403 for all
    other roles.

    Note: This route is intentionally kept simple for Day 1 testing.
    Replace with a real patient dashboard endpoint in Day 2.
    """
    return {"message": "Patient access confirmed", "user_id": str(current_user.id)}
