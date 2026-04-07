"""app/ml/scorer.py — Per-user gait anomaly scoring using the trained autoencoder.

Loads model + scaler from MinIO, computes reconstruction error for a single
session, and normalises it to a 0–1 anomaly score.

Normalisation strategy
-----------------------
Raw MSE reconstruction error is sigmoid-scaled so that:
  - score ≈ 0.0  → reconstruction error very close to the user's training mean
  - score ≈ 1.0  → reconstruction error is far above the training distribution

We use a simple sigmoid over the ratio (raw_error / expected_error_scale) where
expected_error_scale is stored alongside the model as the 95th-percentile
reconstruction error observed during training. This is serialised into the
scaler .pkl alongside the (2, 12) min-max array.

Threshold: anomaly_score > ANOMALY_THRESHOLD → is_anomaly = True
"""

from __future__ import annotations

import logging
from uuid import UUID

import numpy as np
import torch

logger = logging.getLogger("nmove.ml.scorer")

ANOMALY_THRESHOLD: float = 0.65


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def score_snapshot(
    snapshot,           # MetricsSnapshot ORM object
    user_id: str | UUID,
) -> tuple[float, bool] | tuple[None, None]:
    """Compute anomaly_score and is_anomaly for one MetricsSnapshot.

    Returns
    -------
    (anomaly_score: float, is_anomaly: bool)  — on success
    (None, None)                               — if no model exists yet or
                                                 feature extraction fails
    """
    from app.ml.minio_model_store import download_model_artifacts
    from app.ml.autoencoder import model_from_bytes, scaler_from_bytes
    from app.ml.features import FEATURE_COLUMNS, apply_scaler

    uid = UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id

    # ── 1. Load model + scaler from MinIO ─────────────────────────────────
    try:
        artifacts = download_model_artifacts(uid)
    except Exception:
        logger.exception("scorer: MinIO download failed for user=%s", uid)
        return None, None

    if artifacts is None:
        logger.debug("scorer: no model for user=%s — skipping", uid)
        return None, None

    model_bytes, scaler_bytes = artifacts

    try:
        model  = model_from_bytes(model_bytes)
        scaler = scaler_from_bytes(scaler_bytes)
    except Exception:
        logger.exception("scorer: deserialisation failed for user=%s", uid)
        return None, None

    # ── 2. Extract feature row ─────────────────────────────────────────────
    row = _extract_feature_row(snapshot, FEATURE_COLUMNS)
    if row is None:
        logger.warning(
            "scorer: snapshot=%s has incomplete features — cannot score", snapshot.id
        )
        return None, None

    # ── 3. Normalise + reconstruct ─────────────────────────────────────────
    row_arr  = np.array(row, dtype=np.float32)               # (12,)
    row_norm = apply_scaler(row_arr[np.newaxis, :], scaler)  # (1, 12)
    x_tensor = torch.tensor(row_norm, dtype=torch.float32)

    with torch.no_grad():
        recon       = model(x_tensor)
        raw_error   = float(((recon - x_tensor) ** 2).mean().item())

    # ── 4. Normalise to 0–1 via sigmoid ───────────────────────────────────
    # scaler array is (2, 12); we pack the training p95 error in scaler[1, 0]
    # if not present (backward compat), fall back to a fixed scale of 0.1
    p95_error = _get_p95_from_scaler(scaler)
    ratio     = raw_error / max(p95_error, 1e-6)
    # sigmoid(5 * ratio - 2.5) maps ratio=0.5 → score≈0.50, ratio=1 → score≈0.924
    anomaly_score = float(1.0 / (1.0 + np.exp(-5.0 * ratio + 2.5)))
    anomaly_score = float(np.clip(anomaly_score, 0.0, 1.0))

    is_anomaly = anomaly_score > ANOMALY_THRESHOLD

    logger.info(
        "scorer: user=%s snapshot=%s raw_err=%.5f anomaly_score=%.3f is_anomaly=%s",
        uid, snapshot.id, raw_error, anomaly_score, is_anomaly,
    )
    return anomaly_score, is_anomaly


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_feature_row(snapshot, feature_columns: list[str]) -> list[float] | None:
    row: list[float] = []
    for col in feature_columns:
        val = getattr(snapshot, col, None)
        if val is None:
            return None
        row.append(float(val))
    return row


def _get_p95_from_scaler(scaler: np.ndarray) -> float:
    """Read the training p95 reconstruction error packed into the scaler array.

    Convention (set by compute_and_pack_p95): scaler shape is (3, FEATURE_DIM)
    when a p95 row is present — row 2 stores the p95 value in position [2, 0].
    Falls back to 0.10 for legacy (2, FEATURE_DIM) scalers.
    """
    if scaler.shape[0] >= 3:
        return float(scaler[2, 0])
    return 0.10   # conservative fallback: score will still work
