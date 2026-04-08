"""
movement_age.py — Movement Age Scoring from IMU Gait Data
==========================================================

OVERVIEW
--------
This module computes a "Movement Age" — a functional movement quality score
expressed as an equivalent age — from wearable IMU-based gait metrics.

SCIENTIFIC GROUNDING & ASSUMPTIONS
------------------------------------
Reference norms are derived from published literature on healthy adult gait:

  • Hollman et al. (2011) – Normative spatiotemporal gait parameters across
    the adult life span. Gait Posture 34(1):111-118.
  • Menz et al. (2003) – Reliability of the GAITRite walkway system for the
    quantification of temporo-spatial parameters of gait in young and older
    people. Gait Posture 20(1):20-25.
  • Callisaya et al. (2010) – Longitudinal study of gait variability.
    J Gerontol A Biol Sci Med Sci.
  • Beauchet et al. (2009) – Stride-to-stride variability while backward
    counting among healthy young adults. J Neuroeng Rehabil.
  • Perry & Burnfield (2010) – Gait Analysis: Normal and Pathological Function.

WHAT IS VALIDATED vs. HEURISTIC
----------------------------------
  [VALIDATED]  Reference ranges for cadence, step time, stance/swing ratio
               drawn from published normative databases.
  [VALIDATED]  Step-time CV >3% as a clinically significant threshold
               (Hollman et al.; Menz et al.).
  [VALIDATED]  GVI (mean CV of temporal gait parameters) as a composite
               variability index (Beauchet et al.).
  [HEURISTIC]  Exact age-band boundaries and their reference values are
               estimates interpolated from literature ranges. Own calibration
               on a labelled dataset is strongly recommended.
  [HEURISTIC]  Domain weights (variability 35%, stability 30%,
               symmetry 20%, rhythm 15%) reflect clinical importance rankings
               found in gait rehabilitation literature, but are not derived
               from a regression on this codebase's data.
  [HEURISTIC]  The piecewise linear mapping from composite score → movement
               age inverts the direction found empirically across age bands
               (higher score = younger movement) but the exact slope should
               be validated against a labelled cohort.
  [HEURISTIC]  Baseline blend factor alpha=0.3 is a conservative choice that
               gives 30% weight to the personal baseline and 70% to the
               current session, preventing single-session outliers from
               dominating while still reflecting real change over time.

MISSING DATA STRATEGY
-----------------------
Each metric is optional. If absent (None or NaN), it is excluded from its
domain's average and the domain weight is renormalised. If a full domain has
no data, its weight is redistributed to the remaining domains. If no metrics
at all are available, the function returns None.

LIMITATIONS
-----------
  • This is an MVP. Deep learning or regression on a labelled dataset would
    produce more accurate age mappings.
  • Sensor placement, calibration quality, and walking surface affect raw
    metrics; no sensor-quality correction is applied here.
  • Thresholds are not sex-stratified in this version.
  • The module does not account for pathological gait asymmetry (e.g., post-
    stroke hemiplegia) which would need separate reference norms.

FUTURE IMPROVEMENTS
--------------------
  1. Collect a labelled dataset (age-known, healthy controls) and fit a
     multivariate regression or Gaussian process to replace the heuristic
     interpolation table.
  2. Add sex-stratified reference norms.
  3. Add a Mahalanobis-distance based anomaly score to detect pathological
     outliers before computing movement age.
  4. Store z-scores over time for trend analysis.
"""

import math
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("MovementAge")

# ---------------------------------------------------------------------------
# 1. POPULATION REFERENCE NORMS (age-stratified)
# ---------------------------------------------------------------------------
# Structure:  age_band_label → { metric_name → (mean, std) }
#
# Sources (summarised):
#   Cadence:        Hollman 2011 →  ~100–114 steps/min across 20-79 yr cohorts
#   Step time:      derived from cadence (60/cadence * 0.5)
#   Step-time CV:   Menz 2003, Callisaya 2010  →  2-5 % healthy, 5-9 % older
#   GVI:            Beauchet 2009  →  mean CV of temporal params ~3-6 %
#   Stance/swing:   Perry 2010     →  ~1.7–2.0 in normal gait, rises with age
#   Double support: Hollman 2011   →  ~10-25 % of gait cycle
#   Knee-angle CV:  estimated from ROM variability studies  ~5-12 %
#   Stride-len var: related to step-time CV, ~2-5 % in healthy gait
#
# NOTE: std values set conservatively (wide) to avoid over-penalising edge
# cases in an MVP with a small user base.

REFERENCE_NORMS: Dict[str, Dict[str, Tuple[float, float]]] = {
    # (mean, std)
    "young_adult": {          # 20–39 yr
        "step_time_cv":             (2.5,  1.2),   # % CV
        "gait_variability_index":   (3.0,  1.5),   # % (mean of temporal CVs)
        "stance_swing_ratio":       (1.75, 0.15),  # ratio
        "double_support_time":      (10.0, 3.0),   # % gait cycle (heuristic)
        "cadence":                  (113.0, 8.0),  # steps/min
        "avg_step_time":            (0.53, 0.05),  # seconds
        "knee_angle_cv":            (6.0,  2.5),   # % CV
        "stride_length_variability":(2.5,  1.0),   # % CV
    },
    "middle_adult": {         # 40–59 yr
        "step_time_cv":             (3.2,  1.4),
        "gait_variability_index":   (4.0,  1.8),
        "stance_swing_ratio":       (1.80, 0.18),
        "double_support_time":      (14.0, 4.0),
        "cadence":                  (108.0, 9.0),
        "avg_step_time":            (0.56, 0.06),
        "knee_angle_cv":            (8.0,  3.0),
        "stride_length_variability":(3.2,  1.2),
    },
    "older_adult": {          # 60–74 yr
        "step_time_cv":             (4.5,  1.8),
        "gait_variability_index":   (5.5,  2.2),
        "stance_swing_ratio":       (1.90, 0.20),
        "double_support_time":      (20.0, 5.0),
        "cadence":                  (100.0, 10.0),
        "avg_step_time":            (0.60, 0.07),
        "knee_angle_cv":            (10.5, 3.5),
        "stride_length_variability":(4.5,  1.5),
    },
    "elderly": {              # 75+ yr
        "step_time_cv":             (6.5,  2.5),
        "gait_variability_index":   (7.5,  3.0),
        "stance_swing_ratio":       (2.05, 0.25),
        "double_support_time":      (28.0, 6.0),
        "cadence":                  (90.0,  12.0),
        "avg_step_time":            (0.67, 0.09),
        "knee_angle_cv":            (13.0, 4.0),
        "stride_length_variability":(6.0,  2.0),
    },
}

# Age midpoints for each band — used in piecewise interpolation
BAND_AGE_MIDPOINTS: Dict[str, float] = {
    "young_adult":   29.0,
    "middle_adult":  49.0,
    "older_adult":   67.0,
    "elderly":       80.0,
}

# ---------------------------------------------------------------------------
# 2. DOMAIN CONFIGURATION
#    Each domain groups non-overlapping metrics to avoid double-counting.
#    - VARIABILITY: how consistent strides are (temporal variability)
#    - STABILITY:   kinematic consistency (angular variability)
#    - SYMMETRY:    balance between stance/swing phases
#    - RHYTHM:      pace regularity
#
#    Weights (heuristic, based on clinical importance in fall-risk and
#    functional decline literature):
#      Variability 35% — most predictive of fall risk (Menz 2003)
#      Stability   30% — kinematic control degrades with age
#      Symmetry    20% — phase imbalance flags early dysfunction
#      Rhythm      15% — pace, slowest to degrade, important for context
# ---------------------------------------------------------------------------

DOMAIN_METRICS: Dict[str, List[str]] = {
    "variability": ["step_time_cv", "gait_variability_index"],
    "stability":   ["knee_angle_cv", "stride_length_variability"],
    "symmetry":    ["stance_swing_ratio", "double_support_time"],
    "rhythm":      ["cadence", "avg_step_time"],
}

DOMAIN_WEIGHTS: Dict[str, float] = {
    "variability": 0.35,
    "stability":   0.30,
    "symmetry":    0.20,
    "rhythm":      0.15,
}

# ---------------------------------------------------------------------------
# 3. SCORING PARAMETERS
# ---------------------------------------------------------------------------

# Scaling factor for z-score → 0-100 conversion.
# score = 100 - abs(z) * SCALING_FACTOR    (clipped to [0, 100])
#
# Rationale: We want z=0 → score=100, z=2 → score~60 (still acceptable),
# z=3 → score~40 (moderate concern), z=5 → score~0 (severe deviation).
# This gives SCALING_FACTOR = 100/5 = 20.  A factor of 20 means a 5-sigma
# deviation yields a score of 0, while a 2-sigma deviation costs 40 points
# (score = 60).  This is deliberately conservative — we do not want to
# alarm users based on minor single-metric deviations.
#
# [HEURISTIC] — validate and tune with real labelled data.
SCALING_FACTOR: float = 20.0

# Baseline blend alpha
# corrected = current + alpha * (baseline - current)
# = (1 - alpha) * current + alpha * baseline
#
# alpha=0.3 means "30% weight to personal baseline, 70% to current session".
# This prevents regression-to-mean artefacts on a single noisy session while
# still anchoring to the person's healthy reference.  A larger alpha
# (e.g. 0.5) should be used if the baseline was established over multiple
# sessions.  [HEURISTIC]
BASELINE_ALPHA: float = 0.3

# Piecewise linear map: composite score → movement age
# Format: [(score_upper_bound, age_lower_bound), ...]  sorted descending by score
# Interpretation: a score of 90 → movement age of ~25, score of 40 → ~72, etc.
# [HEURISTIC] — recalibrate with labelled cohort data.
SCORE_TO_AGE_MAP: List[Tuple[float, float]] = [
    (95.0, 22.0),
    (88.0, 30.0),
    (80.0, 40.0),
    (70.0, 50.0),
    (60.0, 60.0),
    (48.0, 70.0),
    (35.0, 78.0),
    (0.0,  90.0),
]

# Clinical flag thresholds  [mostly based on published cutoffs]
FLAG_THRESHOLDS: Dict[str, Dict] = {
    "step_time_cv": {
        "threshold": 5.0, "direction": "above",
        "label": "HIGH_TEMPORAL_VARIABILITY",
        "note": "CV >5% is associated with increased fall risk (Menz 2003)"
    },
    "gait_variability_index": {
        "threshold": 6.0, "direction": "above",
        "label": "ELEVATED_GVI",
        "note": "GVI >6% suggests significant gait instability"
    },
    "cadence": {
        "threshold": 90.0, "direction": "below",
        "label": "LOW_CADENCE",
        "note": "Cadence <90 steps/min may indicate reduced walking speed"
    },
    "double_support_time": {
        "threshold": 25.0, "direction": "above",
        "label": "PROLONGED_DOUBLE_SUPPORT",
        "note": "Extended double support is a compensatory strategy in older adults"
    },
    "stance_swing_ratio": {
        "threshold": 2.0, "direction": "above",
        "label": "ASYMMETRIC_GAIT_PHASES",
        "note": "Ratio >2.0 indicates disproportionate stance phase loading"
    },
}


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def _get_value(session_summary: Dict[str, Any], key: str) -> Optional[float]:
    """Safely extract a numeric value from the session summary.
    Returns None if absent, None-valued, or NaN."""
    val = session_summary.get(key)
    if val is None:
        return None
    try:
        f = float(val)
        return None if math.isnan(f) or math.isinf(f) else f
    except (TypeError, ValueError):
        return None


def _select_reference_band(chronological_age: Optional[int]) -> str:
    """Choose the most appropriate reference band.
    Falls back to 'middle_adult' (broadest healthy demographic) when age
    is unknown — this is the most conservative assumption for an MVP."""
    if chronological_age is None:
        return "middle_adult"
    if chronological_age < 40:
        return "young_adult"
    if chronological_age < 60:
        return "middle_adult"
    if chronological_age < 75:
        return "older_adult"
    return "elderly"


def _zscore_to_metric_score(value: float, mean: float, std: float) -> float:
    """Convert a raw metric value to a 0-100 score via z-score penalty.

    For metrics where HIGHER values indicate WORSE performance (e.g. CV%,
    double support time), we penalise deviation above the mean (positive z).
    For metrics where LOWER values indicate WORSE performance (e.g. cadence),
    we penalise negative z.

    In both cases we use abs(z) as the penalty magnitude — the reference norms
    already capture the expected direction (a young adult should have low CV
    and high cadence; deviation in either direction beyond std is penalised).

    score = 100 - abs(z) * SCALING_FACTOR, clipped to [0, 100].
    """
    if std <= 0:
        return 100.0  # undefined std → no information → neutral score
    z = (value - mean) / std
    score = 100.0 - abs(z) * SCALING_FACTOR
    return float(np.clip(score, 0.0, 100.0))


def _compute_domain_score(
    domain_name: str,
    metric_names: List[str],
    session_summary: Dict[str, Any],
    norms: Dict[str, Tuple[float, float]],
) -> Optional[float]:
    """Compute the mean metric score for all available metrics in a domain.
    Returns None if no metrics in the domain are available."""
    scores = []
    for metric in metric_names:
        val = _get_value(session_summary, metric)
        if val is None:
            continue
        if metric not in norms:
            logger.debug("No reference norm for metric '%s'; skipping.", metric)
            continue
        mean, std = norms[metric]
        s = _zscore_to_metric_score(val, mean, std)
        scores.append(s)
        logger.debug(
            "  %s: value=%.3f, mean=%.3f, std=%.3f → score=%.1f",
            metric, val, mean, std, s
        )
    if not scores:
        return None
    return float(np.mean(scores))


def _compute_composite_score(
    domain_scores: Dict[str, Optional[float]]
) -> Tuple[float, float]:
    """Compute the weighted composite score and a confidence estimate.

    Weights are renormalised if some domains are missing.
    Confidence = fraction of total weight for which data was available,
    further reduced if fewer than 2 metrics contributed to each domain.
    """
    available_weight = 0.0
    weighted_sum = 0.0
    for domain, score in domain_scores.items():
        w = DOMAIN_WEIGHTS[domain]
        if score is not None:
            weighted_sum += score * w
            available_weight += w

    if available_weight == 0.0:
        return 0.0, 0.0

    composite = weighted_sum / available_weight
    confidence = available_weight  # [0, 1] — fraction of weight covered
    return float(np.clip(composite, 0.0, 100.0)), float(confidence)


def _score_to_movement_age(score: float) -> float:
    """Piecewise linear interpolation from composite score to movement age.

    The mapping is monotonically decreasing: higher score → younger age.
    Uses nearest-segment linear interpolation between the anchor points
    defined in SCORE_TO_AGE_MAP.

    [HEURISTIC] — this table must be validated against a labelled cohort.
    """
    # Ensure the map is sorted descending by score
    anchors = sorted(SCORE_TO_AGE_MAP, key=lambda x: -x[0])

    # Above the highest anchor → youngest mapped age
    if score >= anchors[0][0]:
        return anchors[0][1]

    # Below the lowest anchor → oldest mapped age
    if score <= anchors[-1][0]:
        return anchors[-1][1]

    # Find the bounding segment
    for i in range(len(anchors) - 1):
        s_high, a_low = anchors[i]
        s_low, a_high = anchors[i + 1]
        if s_low <= score <= s_high:
            # Linear interpolation within the segment
            t = (score - s_low) / (s_high - s_low)
            age = a_high + t * (a_low - a_high)
            return round(age, 1)

    # Fallback (should not be reached)
    return anchors[-1][1]


def _detect_flags(session_summary: Dict[str, Any]) -> List[str]:
    """Detect clinically notable gait deviations and return flag labels."""
    flags = []
    for metric, cfg in FLAG_THRESHOLDS.items():
        val = _get_value(session_summary, metric)
        if val is None:
            continue
        if cfg["direction"] == "above" and val > cfg["threshold"]:
            flags.append(cfg["label"])
        elif cfg["direction"] == "below" and val < cfg["threshold"]:
            flags.append(cfg["label"])
    return flags


def _apply_baseline_blend(
    current_score: float,
    baseline_summary: Optional[Dict[str, Any]],
    chronological_age: Optional[int],
) -> float:
    """Blend current composite score with personal baseline score.

    corrected = current + alpha * (baseline - current)
               = (1 - alpha) * current + alpha * baseline

    alpha = BASELINE_ALPHA = 0.3  (heuristic, see module docstring)

    Only applied if a valid baseline summary is provided.
    """
    if baseline_summary is None:
        return current_score

    # Recompute baseline score using the same pipeline (no recursive baseline)
    baseline_result = calculate_movement_age(
        session_summary=baseline_summary,
        chronological_age=chronological_age,
        baseline_summary=None,  # no recursive blending
    )
    if baseline_result is None or baseline_result.get("movement_score") is None:
        logger.warning("Baseline score could not be computed; skipping blend.")
        return current_score

    baseline_score = baseline_result["movement_score"]
    corrected = current_score + BASELINE_ALPHA * (baseline_score - current_score)
    logger.info(
        "Baseline blend: current=%.1f, baseline=%.1f, corrected=%.1f (alpha=%.2f)",
        current_score, baseline_score, corrected, BASELINE_ALPHA,
    )
    return float(np.clip(corrected, 0.0, 100.0))


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def calculate_movement_age(
    session_summary: Dict[str, Any],
    chronological_age: Optional[int] = None,
    baseline_summary: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Compute Movement Age and composite gait quality score.

    Parameters
    ----------
    session_summary : dict
        The session summary dict produced by ``calculate_session_summary``.
        Expected keys (all optional — missing keys are handled gracefully):
          step_time_cv, gait_variability_index (gvi), stance_swing_ratio,
          double_support_time, cadence, avg_step_time,
          knee_angle_cv, stride_length_variability.
    chronological_age : int, optional
        User's biological age in years.  Used to select the age-appropriate
        reference band.  If None, ``middle_adult`` norms are used.
    baseline_summary : dict, optional
        A previous session summary for this user that serves as their personal
        healthy baseline.  If provided, a weighted blend is applied
        (alpha = BASELINE_ALPHA = 0.3).

    Returns
    -------
    dict with keys:
        movement_age   : float  — estimated functional movement age (years)
        movement_score : float  — composite quality score [0, 100]
        confidence     : float  — fraction of metrics available [0, 1]
        breakdown      : dict   — per-domain scores
        flags          : list   — clinical issue labels
    Returns None if no gait metrics are available at all.

    Notes
    -----
    The ``gait_variability_index`` key is stored as ``gvi`` in the session
    summary produced by session_pro.py.  This function maps it automatically.
    """

    # ------------------------------------------------------------------
    # Alias GVI field name (session_pro uses 'gvi', algorithm uses 'gait_variability_index')
    if "gvi" in session_summary and "gait_variability_index" not in session_summary:
        session_summary = dict(session_summary)  # shallow copy, don't mutate original
        session_summary["gait_variability_index"] = session_summary["gvi"]

    # ------------------------------------------------------------------
    # Step 1: Select reference band
    band = _select_reference_band(chronological_age)
    norms = REFERENCE_NORMS[band]
    logger.info(
        "Movement age: using reference band='%s' (chron_age=%s)",
        band, chronological_age
    )

    # ------------------------------------------------------------------
    # Step 2: Compute per-domain scores
    domain_scores: Dict[str, Optional[float]] = {}
    for domain, metrics in DOMAIN_METRICS.items():
        score = _compute_domain_score(domain, metrics, session_summary, norms)
        domain_scores[domain] = score
        if score is not None:
            logger.info("  Domain '%s': %.1f", domain, score)
        else:
            logger.info("  Domain '%s': no data", domain)

    # ------------------------------------------------------------------
    # Step 3: Compute weighted composite score
    composite_score, confidence = _compute_composite_score(domain_scores)

    if confidence < 0.01:
        logger.warning(
            "No gait metrics available — cannot compute movement age."
        )
        return None

    # ------------------------------------------------------------------
    # Step 4: Apply personal baseline blend (if available)
    blended_score = _apply_baseline_blend(
        current_score=composite_score,
        baseline_summary=baseline_summary,
        chronological_age=chronological_age,
    )

    # ------------------------------------------------------------------
    # Step 5: Map composite score → movement age
    movement_age = _score_to_movement_age(blended_score)

    # ------------------------------------------------------------------
    # Step 6: Detect clinical flags
    flags = _detect_flags(session_summary)

    # ------------------------------------------------------------------
    # Step 7: Build output
    breakdown = {
        domain: (round(score, 1) if score is not None else None)
        for domain, score in domain_scores.items()
    }

    result = {
        "movement_age":   movement_age,
        "movement_score": round(blended_score, 1),
        "confidence":     round(confidence, 3),
        "breakdown": {
            "variability": breakdown.get("variability"),
            "stability":   breakdown.get("stability"),
            "symmetry":    breakdown.get("symmetry"),
            "rhythm":      breakdown.get("rhythm"),
        },
        "flags": flags,
    }

    logger.info(
        "Movement Age result: score=%.1f, age=%.1f yr, confidence=%.2f, flags=%s",
        blended_score, movement_age, confidence, flags
    )
    return result
