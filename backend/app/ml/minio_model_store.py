"""app/ml/minio_model_store.py — MinIO helpers for ML model persistence.

Bucket: ``nmove-models``
Layout:
    models/{user_id}/autoencoder.pkl   — torch state_dict bytes
    models/{user_id}/scaler.pkl        — numpy (2, N) min-max scaler

Functions are synchronous — designed for use inside Celery tasks.
"""

from __future__ import annotations

import io
import logging
from uuid import UUID

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

logger = logging.getLogger("nmove.ml.minio_store")

MODELS_BUCKET = "nmove-models"


# ─────────────────────────────────────────────────────────────────────────────
# Internal client
# ─────────────────────────────────────────────────────────────────────────────

def _get_client() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD,
        secure=settings.MINIO_SECURE,
    )


def _ensure_bucket() -> None:
    client = _get_client()
    try:
        if not client.bucket_exists(MODELS_BUCKET):
            client.make_bucket(MODELS_BUCKET)
            logger.info("Created MinIO bucket '%s'", MODELS_BUCKET)
    except S3Error as exc:
        logger.error("MinIO bucket error for '%s': %s", MODELS_BUCKET, exc)
        raise


# ─────────────────────────────────────────────────────────────────────────────
# Upload
# ─────────────────────────────────────────────────────────────────────────────

def upload_model_artifacts(
    user_id: UUID,
    model_bytes: bytes,
    scaler_bytes: bytes,
) -> tuple[str, str]:
    """Upload model and scaler bytes to MinIO.

    Returns (model_path, scaler_path) — the MinIO object names.
    """
    _ensure_bucket()
    client = _get_client()

    model_path  = f"models/{user_id}/autoencoder.pkl"
    scaler_path = f"models/{user_id}/scaler.pkl"

    def _put(object_name: str, data: bytes) -> None:
        stream = io.BytesIO(data)
        client.put_object(
            bucket_name=MODELS_BUCKET,
            object_name=object_name,
            data=stream,
            length=len(data),
            content_type="application/octet-stream",
        )

    _put(model_path, model_bytes)
    _put(scaler_path, scaler_bytes)

    return model_path, scaler_path


# ─────────────────────────────────────────────────────────────────────────────
# Download
# ─────────────────────────────────────────────────────────────────────────────

def download_model_artifacts(
    user_id: UUID,
) -> tuple[bytes, bytes] | None:
    """Download model and scaler bytes from MinIO.

    Returns ``(model_bytes, scaler_bytes)`` or ``None`` if either object is
    missing (i.e. the user has no trained model yet).
    """
    client = _get_client()
    model_path  = f"models/{user_id}/autoencoder.pkl"
    scaler_path = f"models/{user_id}/scaler.pkl"

    try:
        model_res  = client.get_object(MODELS_BUCKET, model_path)
        model_bytes = model_res.read()
        model_res.close()

        scaler_res  = client.get_object(MODELS_BUCKET, scaler_path)
        scaler_bytes = scaler_res.read()
        scaler_res.close()

        return model_bytes, scaler_bytes

    except S3Error as exc:
        if exc.code in ("NoSuchKey", "NoSuchBucket"):
            logger.debug("No model found for user=%s in MinIO", user_id)
            return None
        logger.error("MinIO download error for user=%s: %s", user_id, exc)
        raise
