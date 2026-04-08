"""Legacy shim for old SQLAlchemy table models.

This isolates legacy pipeline imports under `app.legacy.*` while modern routers
and services use `app.models.*`.
"""

from app.data.tables import *  # noqa: F403,F401

