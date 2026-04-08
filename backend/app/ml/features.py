"""app/ml/features.py — Feature engineering for per-user gait autoencoder.

Feature vector (12 dims), organized by biomechanical domain:

  Rhythm & Pace      [0–2] : cadence, stride_length, avg_speed
  Joint Mechanics    [3–5] : hip_rotation_rom, ankle_pushoff_proxy, vertical_oscillation
  Variability        [6–7] : stride_time_cv, trunk_sway_rms
  Symmetry & Phases  [8–11]: symmetry_score, stance_phase_pct, double_support_pct,
                             movement_age_delta

Normalization: per-user min-max, stored as a numpy array of shape (2, 12)
               where row 0 = min, row 1 = max, for each feature.

Edge cases handled:
  - Fewer than 7 complete sessions → returns None (caller should skip training)
  - bio_age is None on any snapshot → returns None (bio_age is required)
  - Any feature column is None on a snapshot → that session is dropped
  - All-zero range on a feature → clamped to 1.0 to avoid division-by-zero
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID

import numpy as np

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger("nmove.ml.features")

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

MIN_SESSIONS = 7        # minimum sessions required to train
MAX_SESSIONS = 20       # cap rolling window to last N sessions

# Ordered list of MetricsSnapshot attribute names that form the feature vector.
# Order MUST NOT change after models are deployed — stored scalers depend on it.
FEATURE_COLUMNS: list[str] = [
    # Rhythm & Pace
    "cadence",
    "stride_length",
    "avg_speed",
    # Joint Mechanics
    "hip_rotation_rom",
    "ankle_pushoff_proxy",
    "vertical_oscillation",
    # Variability
    "stride_time_cv",
    "trunk_sway_rms",
    # Symmetry & Phases
    "symmetry_score",
    "stance_phase_pct",
    "double_support_pct",
    "movement_age_delta",
]

FEATURE_DIM: int = len(FEATURE_COLUMNS)   # 12


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def build_feature_matrix(
    user_id: str | UUID,
    db: "Session",
    n: int = MAX_SESSIONS,
) -> np.ndarray | None:
    """Return a float32 matrix of shape (n_sessions, FEATURE_DIM) for *user_id*.

    Pulls the last ``n`` *done* sessions with a MetricsSnapshot.
    Returns ``None`` if fewer than MIN_SESSIONS valid snapshots exist or if
    any snapshot is missing ``bio_age`` (which is a required profile field).

    The returned matrix is **raw** (not normalized). Call
    :func:`fit_scaler` / :func:`apply_scaler` separately.
    """
    from app.models.gait_session import GaitSession, SessionStatus
    from app.models.metrics_snapshot import MetricsSnapshot

    uid = UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id

    # Pull the most recent `n` sessions (done state only)
    snapshots = (
        db.query(MetricsSnapshot)
        .join(GaitSession, GaitSession.id == MetricsSnapshot.gait_session_id)
        .filter(
            GaitSession.user_id == uid,
            GaitSession.status == SessionStatus.done,
        )
        .order_by(MetricsSnapshot.calculated_at.desc())
        .limit(n)
        .all()
    )

    # Oldest-first so the autoencoder sees chronological progression
    snapshots = list(reversed(snapshots))

    if len(snapshots) < MIN_SESSIONS:
        logger.info(
            "user=%s has %d snapshots (<%d) — skipping ML training",
            uid, len(snapshots), MIN_SESSIONS,
        )
        return None

    rows: list[list[float]] = []
    for snap in snapshots:
        # bio_age is required — skip training if any session lacks it
        if snap.bio_age is None:
            logger.warning(
                "user=%s snapshot=%s missing bio_age — skipping ML training",
                uid, snap.id,
            )
            return None

        row = _extract_row(snap)
        if row is None:
            # A non-nullable extended feature is still None (old snapshot
            # recorded before migration); skip training for now
            logger.warning(
                "user=%s snapshot=%s has None extended feature — skipping",
                uid, snap.id,
            )
            return None

        rows.append(row)

    if len(rows) < MIN_SESSIONS:
        return None

    return np.array(rows, dtype=np.float32)   # (n, 12)


def fit_scaler(matrix: np.ndarray) -> np.ndarray:
    """Compute per-feature min/max from *matrix*.

    Returns a (2, FEATURE_DIM) float32 array: row 0 = min, row 1 = max.
    Columns where min == max get max set to min + 1.0 to avoid zero-division.
    """
    feat_min = matrix.min(axis=0)                   # (12,)
    feat_max = matrix.max(axis=0)                   # (12,)
    zero_range = feat_max == feat_min
    feat_max[zero_range] = feat_min[zero_range] + 1.0
    return np.stack([feat_min, feat_max], axis=0).astype(np.float32)  # (2, 12)


def apply_scaler(matrix: np.ndarray, scaler: np.ndarray) -> np.ndarray:
    """Min-max normalize *matrix* using a scaler from :func:`fit_scaler`."""
    feat_min = scaler[0]
    feat_max = scaler[1]
    return (matrix - feat_min) / (feat_max - feat_min + 1e-9)


def inverse_scaler(matrix: np.ndarray, scaler: np.ndarray) -> np.ndarray:
    """Undo min-max normalization."""
    feat_min = scaler[0]
    feat_max = scaler[1]
    return matrix * (feat_max - feat_min + 1e-9) + feat_min


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_row(snap) -> list[float] | None:
    """Extract the feature row for one MetricsSnapshot.

    Returns ``None`` if any required column is missing (None).
    """
    row: list[float] = []
    for col in FEATURE_COLUMNS:
        val = getattr(snap, col, None)
        if val is None:
            return None
        row.append(float(val))
    return row
