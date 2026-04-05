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

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health", tags=["Health"], summary="Service liveness probe")
async def health() -> dict:
    """Return a simple liveness response including the current environment."""
    return {"status": "ok", "app": "NMove", "env": settings.APP_ENV}
