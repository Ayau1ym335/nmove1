"""app/core/security.py — Password hashing, JWT token creation, and refresh token generation."""
import hashlib
import secrets
from datetime import datetime, timedelta

import bcrypt
from fastapi import HTTPException, status
from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing (direct bcrypt — passlib 1.7.4 is incompatible with bcrypt >= 4)
# ---------------------------------------------------------------------------


def hash_password(plain: str) -> str:
    """Hash a plain-text password with bcrypt. Returns str."""
    rounds = getattr(settings, "BCRYPT_ROUNDS", 12)
    salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the stored bcrypt hash. Never raises."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT access token
# ---------------------------------------------------------------------------


def create_access_token(user_id: object, role: str) -> str:
    """Create a signed JWT access token.

    Payload:
        sub  — user UUID (str)
        role — UserRole value
        iat  — issued-at (UTC)
        exp  — expiry (UTC, now + ACCESS_TOKEN_EXPIRE_MINUTES)
        type — "access"

    Note: python-jose requires timezone-naive UTC datetimes in the payload.
    datetime.utcnow() is used intentionally here (not datetime.now(UTC))
    because jose's internal comparisons use naive UTC datetimes.
    """
    now = datetime.utcnow()  # intentionally naive UTC — required by python-jose
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token.

    Raises HTTPException 401 if the token is expired or otherwise invalid.
    Returns the full payload dict on success.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Enforce token type — reject refresh tokens on protected routes
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


# ---------------------------------------------------------------------------
# Opaque refresh token
# ---------------------------------------------------------------------------


def generate_refresh_token() -> tuple[str, str]:
    """Generate a cryptographically-secure opaque refresh token.

    Returns:
        (raw_token, token_hash)

    The raw token (secrets.token_urlsafe(64)) is sent to the client.
    Only the SHA-256 hex digest is persisted (DB + Redis) — the raw token
    is never stored, so a DB/Redis breach does not expose usable tokens.
    """
    raw = secrets.token_urlsafe(64)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    return raw, token_hash


# Alias kept for backward-compat with existing router code
def create_refresh_token() -> tuple[str, str]:
    """Alias for generate_refresh_token()."""
    return generate_refresh_token()


def hash_refresh_token(raw_token: str) -> str:
    """Compute the SHA-256 hex digest of a raw refresh token."""
    return hashlib.sha256(raw_token.encode()).hexdigest()
