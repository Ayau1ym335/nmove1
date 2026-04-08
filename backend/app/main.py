"""app/main.py — FastAPI application entry point for NMove."""
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.redis import redis_client
from app.routers import auth as auth_router_module
from app.routers.sessions import router as sessions_router
from app.routers.dashboard import router as dashboard_router
from app.routers.trends import router as trends_router
from app.routers.doctor import router as doctor_router

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run startup checks and clean up on shutdown."""
    # Startup
    logger.info("NMove API starting...")
    try:
        await redis_client.ping()
        logger.info("Redis connected successfully.")
    except Exception as exc:  # pragma: no cover
        logger.error("Redis connection failed: %s", exc)

    # Ensure MinIO buckets exist (idempotent — safe to call on every restart)
    try:
        import asyncio as _asyncio
        from app.services.minio_service import ensure_bucket_exists
        from app.ml.minio_model_store import _ensure_bucket as ensure_models_bucket
        await _asyncio.to_thread(ensure_bucket_exists)
        await _asyncio.to_thread(ensure_models_bucket)
        logger.info("MinIO buckets verified.")
    except Exception as exc:  # pragma: no cover
        logger.warning("MinIO bucket init failed (non-fatal at startup): %s", exc)


    yield  # Application is live and serving requests

    # Shutdown (graceful)
    logger.info("NMove API shutting down...")
    await redis_client.aclose()
    logger.info("Redis connection closed.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="NMove API",
    version=settings.APP_VERSION,
    description="NMove gait analysis backend API.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth_router_module.router)   # prefix="/auth" set inside router
app.include_router(sessions_router)             # prefix="/sessions" set inside router
app.include_router(dashboard_router)            # prefix="/dashboard" set inside router
app.include_router(trends_router)               # prefix="/trends" set inside router
app.include_router(doctor_router)               # prefix="/doctor" set inside router

# ---------------------------------------------------------------------------
# Health check — full readiness probe: DB + Redis + MinIO
# ---------------------------------------------------------------------------


@app.get("/health", tags=["Health"], summary="Full readiness probe — DB, Redis, MinIO")
async def health() -> dict:
    """Return 200 if all backing services are healthy; 503 otherwise.
    Never exposes raw exception messages in the response body.
    """
    from fastapi import HTTPException
    from sqlalchemy import text as sa_text
    from app.db.session import AsyncSessionLocal

    checks: dict[str, str] = {}
    all_ok = True

    # ── DB ────────────────────────────────────────────────────────────────────
    try:
        async with AsyncSessionLocal() as _db:
            await _db.execute(sa_text("SELECT 1"))
        checks["db"] = "ok"
    except Exception:
        logger.exception("Health: DB check failed")
        checks["db"] = "error"
        all_ok = False

    # ── Redis ─────────────────────────────────────────────────────────────────
    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception:
        logger.exception("Health: Redis check failed")
        checks["redis"] = "error"
        all_ok = False

    # ── MinIO ─────────────────────────────────────────────────────────────────
    try:
        import asyncio as _asyncio
        from app.services.minio_service import _get_client, BUCKET_NAME
        _mc = _get_client()
        await _asyncio.to_thread(_mc.bucket_exists, BUCKET_NAME)
        checks["minio"] = "ok"
    except Exception:
        logger.exception("Health: MinIO check failed")
        checks["minio"] = "error"
        all_ok = False

    payload = {
        "status": "ok" if all_ok else "degraded",
        "app": "NMove",
        "env": settings.APP_ENV,
        "checks": checks,
    }
    if not all_ok:
        raise HTTPException(status_code=503, detail=payload)
    return payload
