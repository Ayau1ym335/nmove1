"""app/ml/trainer.py — Celery-compatible training trigger for per-user autoencoder.

Entry point: ``maybe_train_model(user_id, db)``

Logic
-----
  sessions < 7            → skip (return without training)
  sessions == 7, 14, 21, ... (multiples of 7) → train / retrain
  sessions in between     → skip (no milestone reached)

The trained model and scaler are persisted to MinIO under:
    models/{user_id}/autoencoder.pkl   — torch state_dict bytes
    models/{user_id}/scaler.pkl        — numpy (3, 12) array
                                         row 0 = per-feature min
                                         row 1 = per-feature max
                                         row 2 = p95 reconstruction error (col 0)

A row is written to the ``user_models`` table with training metadata.
All exceptions are caught and logged — training failure MUST NOT propagate to
the Celery task that called this function.
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING
from uuid import UUID

import numpy as np

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger("nmove.ml.trainer")


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def maybe_train_model(user_id: str | UUID, db: "Session") -> None:
    """Train or retrain the per-user gait autoencoder if conditions are met.

    This function is designed to be called from within a synchronous Celery
    task. It shares the existing ``db`` session (from ``get_sync_db``).

    Parameters
    ----------
    user_id : str or UUID — the patient's user ID
    db      : sqlalchemy.orm.Session — an **open** synchronous session
    """
    try:
        _run_training(user_id, db)
    except Exception:
        logger.exception(
            "maybe_train_model: unhandled error for user=%s — training skipped",
            user_id,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Internal implementation
# ─────────────────────────────────────────────────────────────────────────────

def _run_training(user_id: str | UUID, db: "Session") -> None:
    from app.ml.features import (
        MIN_SESSIONS,
        build_feature_matrix,
        fit_scaler,
        apply_scaler,
    )
    from app.ml.autoencoder import (
        train_autoencoder,
        model_to_bytes,
        scaler_to_bytes,
    )
    from app.ml.minio_model_store import upload_model_artifacts, MODELS_BUCKET
    from app.models.user_model import UserModel
    from app.models.gait_session import GaitSession, SessionStatus
    from app.models.metrics_snapshot import MetricsSnapshot

    uid = UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id

    # ── 1. Count completed sessions ──────────────────────────────────────────
    n_sessions: int = (
        db.query(GaitSession)
        .filter(
            GaitSession.user_id == uid,
            GaitSession.status == SessionStatus.done,
        )
        .count()
    )

    if n_sessions < MIN_SESSIONS:
        logger.debug(
            "user=%s has %d done sessions (<%d) — skipping training",
            uid, n_sessions, MIN_SESSIONS,
        )
        return

    # Retrain at session count == 7, 14, 21, ... (multiples of MIN_SESSIONS)
    if n_sessions % MIN_SESSIONS != 0:
        logger.debug(
            "user=%s: %d sessions (not a retrain milestone) — skipping",
            uid, n_sessions,
        )
        return

    logger.info(
        "user=%s: %s model — %d sessions available",
        uid,
        "initial" if n_sessions == MIN_SESSIONS else "rolling retrain",
        n_sessions,
    )

    # ── 2. Build feature matrix ──────────────────────────────────────────────
    X_raw = build_feature_matrix(uid, db)
    if X_raw is None:
        logger.info("user=%s: feature matrix returned None — skipping training", uid)
        return

    # ── 3. Fit scaler + normalise ────────────────────────────────────────────
    scaler = fit_scaler(X_raw)          # (2, 12) numpy
    X_norm = apply_scaler(X_raw, scaler)

    # ── 4. Train autoencoder ─────────────────────────────────────────────────
    model, losses = train_autoencoder(X_norm)

    # ── 4b. Compute p95 reconstruction error and pack into scaler (row 2) ───
    # scorer.py uses this as the normalisation scale for anomaly scoring.
    import torch
    with torch.no_grad():
        x_t   = torch.tensor(X_norm, dtype=torch.float32)
        recon = model(x_t)
        errors = ((recon - x_t) ** 2).mean(dim=1).numpy()   # (n,)
    p95 = float(np.percentile(errors, 95)) if len(errors) > 0 else 0.10
    p95 = max(p95, 1e-6)
    # Extend scaler to (3, FEATURE_DIM): row 2 = p95 packed in position [:, 0]
    p95_row = np.zeros((1, scaler.shape[1]), dtype=np.float32)
    p95_row[0, 0] = p95
    scaler = np.vstack([scaler, p95_row])   # (3, 12)

    # ── 5. Serialise ─────────────────────────────────────────────────────────
    model_bytes  = model_to_bytes(model)
    scaler_bytes = scaler_to_bytes(scaler)

    # ── 6. Upload to MinIO ───────────────────────────────────────────────────
    model_path, scaler_path = upload_model_artifacts(uid, model_bytes, scaler_bytes)

    logger.info(
        "user=%s: model uploaded → %s | scaler → %s",
        uid, model_path, scaler_path,
    )

    # ── 7. Persist training metadata in DB ───────────────────────────────────
    record = UserModel(
        id=uuid.uuid4(),
        user_id=uid,
        model_type="autoencoder",
        n_sessions=X_raw.shape[0],
        minio_path=model_path,
        scaler_path=scaler_path,
    )
    db.add(record)
    db.flush()   # flush within the caller's transaction; commit happens in caller

    logger.info(
        "user=%s: UserModel row persisted (id=%s, n_sessions=%d, final_loss=%.6f)",
        uid, record.id, X_raw.shape[0], losses[-1],
    )
