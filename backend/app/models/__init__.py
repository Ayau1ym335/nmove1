# backend/app/models/__init__.py
"""app/models/__init__.py — Import all models so Alembic sees them on Base.metadata."""
from app.models.user import User, UserRole
from app.models.session import AuthSession
from app.models.gait_session import GaitSession
from app.models.gait_reading import GaitReading
from app.models.metrics_snapshot import MetricsSnapshot, InterpretationStatus
from app.models.exercise import Exercise, ExerciseDifficulty
from app.models.user_model import UserModel

__all__ = [
    "User",
    "UserRole",
    "AuthSession",
    "GaitSession",
    "GaitReading",
    "MetricsSnapshot",
    "InterpretationStatus",
    "Exercise",
    "ExerciseDifficulty",
    "UserModel",
]
