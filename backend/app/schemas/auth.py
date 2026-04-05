"""app/schemas/auth.py — Pydantic v2 schemas for auth endpoints."""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    """Body for POST /auth/register."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: Literal["patient", "doctor"] = "patient"
    full_name: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Require at least one digit and at least one letter."""
        has_digit = any(c.isdigit() for c in v)
        has_letter = any(c.isalpha() for c in v)
        if not has_digit:
            raise ValueError("Password must contain at least one digit.")
        if not has_letter:
            raise ValueError("Password must contain at least one letter.")
        return v

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    """Body for POST /auth/login."""

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

    model_config = ConfigDict(from_attributes=True)


class RefreshRequest(BaseModel):
    """Body for POST /auth/refresh."""

    refresh_token: str

    @field_validator("refresh_token")
    @classmethod
    def validate_refresh_token(cls, v: str) -> str:
        """Strip whitespace and enforce minimum length of 10 characters."""
        stripped = v.strip()
        if len(stripped) < 10:
            raise ValueError("Refresh token must be at least 10 characters.")
        return stripped


class LogoutRequest(BaseModel):
    """Body for POST /auth/logout."""

    refresh_token: str


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class UserOut(BaseModel):
    """Safe user representation — never includes password fields."""

    id: uuid.UUID
    email: str
    role: UserRole
    full_name: str | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """JWT access token + opaque refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires


class RefreshResponse(BaseModel):
    """Response for POST /auth/refresh — rotated token pair."""

    access_token: str
    refresh_token: str            # new rotated refresh token
    token_type: str = "bearer"
    expires_in: int               # seconds until access token expires


class RegisterResponse(BaseModel):
    """Returned on successful registration."""

    user: UserOut
    message: str = "Registration successful"
