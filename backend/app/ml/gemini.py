"""app/ml/gemini.py — Gemini Flash AI commentary on per-user gait analysis.

Two prompt templates:
  - patient  : plain language, encouraging, actionable
  - doctor   : clinical language, metric-specific, flags anomalies

Redis caching:
  - Key    : gemini:insight:{user_id}:{snapshot_id}
  - TTL    : 3600s (1 hour)
  - Cache is invalidated on new session → next call regenerates

Entry point: ``get_gait_insight(user_id, snapshot, trend_direction, audience)``
"""

from __future__ import annotations

import json
import logging
from typing import Literal
from uuid import UUID

logger = logging.getLogger("nmove.ml.gemini")

CACHE_TTL = 3600   # 1 hour


# ─────────────────────────────────────────────────────────────────────────────
# Prompt templates
# ─────────────────────────────────────────────────────────────────────────────

_PATIENT_SYSTEM = (
    "You are NMove, a friendly personal movement coach. "
    "Explain gait analysis results in simple, encouraging language. "
    "Avoid medical jargon. Use short paragraphs. "
    "If something is abnormal, explain what to do, not why it's bad. "
    "Keep the response under 200 words."
)

_DOCTOR_SYSTEM = (
    "You are a clinical gait analysis assistant for NMove. "
    "Provide a concise clinical summary of the patient's gait metrics. "
    "Reference specific metric values and flag any that are outside normal ranges. "
    "Use biomechanical terminology. Highlight anomaly detection findings. "
    "Keep the response under 300 words."
)

_PATIENT_PROMPT = """
Patient movement summary:
- Movement age: {movement_age} years (biological age: {bio_age})
- Cadence: {cadence} steps/min | Speed: {avg_speed} m/s
- Step symmetry: {symmetry_score:.2f} | Stability: {stability_score:.2f}
- Stride consistency (CV%): {stride_time_cv} | Trunk sway: {trunk_sway_rms}
- Stance phase: {stance_phase_pct}% | Double support: {double_support_pct}%
- Trend: {trend_direction}
- Anomaly detected: {is_anomaly} (score: {anomaly_score})

Write a short, friendly update for the patient about their movement health this session.
"""

_DOCTOR_PROMPT = """
Clinical gait analysis report:
Patient: {user_id}
Session metrics:
  Rhythm & Pace     — Cadence: {cadence} spm | Speed: {avg_speed} m/s | Stride length: {stride_length} m
  Joint Mechanics   — Hip ROM: {hip_rotation_rom}° | Ankle pushoff: {ankle_pushoff_proxy} m/s² | Vert. osc.: {vertical_oscillation} m/s²
  Variability       — Stride CV: {stride_time_cv}% | Trunk sway RMS: {trunk_sway_rms} m/s²
  Symmetry & Phases — Symmetry: {symmetry_score:.3f} | Stance: {stance_phase_pct}% | Double support: {double_support_pct}%
  Movement age      — {movement_age} yrs (Δ vs bio-age {bio_age}: {movement_age_delta})
  Autoencoder       — Anomaly score: {anomaly_score} | Flagged: {is_anomaly}
  Trend             — {trend_direction}

Provide a clinical interpretation. Flag any clinically significant deviations.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

async def get_gait_insight(
    user_id: UUID,
    snapshot,           # MetricsSnapshot ORM object
    trend_direction: str | None,
    audience: Literal["patient", "doctor"] = "patient",
) -> str:
    """Return a Gemini-generated gait insight string.

    Checks Redis cache first (TTL 1h). Falls back to a static message if
    Gemini is unavailable or the API key is not configured.
    """
    cache_key = f"gemini:insight:{user_id}:{snapshot.id}:{audience}"

    # ── 1. Cache check ────────────────────────────────────────────────────────
    cached = await _cache_get(cache_key)
    if cached:
        logger.debug("Gemini cache HIT user=%s audience=%s", user_id, audience)
        return cached

    logger.debug("Gemini cache MISS user=%s audience=%s", user_id, audience)

    # ── 2. Build context dict ─────────────────────────────────────────────────
    ctx = _build_context(user_id, snapshot, trend_direction)

    # ── 3. Call Gemini ────────────────────────────────────────────────────────
    try:
        text = await _call_gemini(ctx, audience)
    except Exception:
        logger.exception("Gemini call failed for user=%s — returning fallback", user_id)
        text = _fallback_message(audience, ctx)

    # ── 4. Cache + return ─────────────────────────────────────────────────────
    await _cache_set(cache_key, text)
    return text


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_context(user_id: UUID, snapshot, trend_direction: str | None) -> dict:
    def _f(attr: str, default: str = "N/A") -> str:
        val = getattr(snapshot, attr, None)
        return str(round(val, 3)) if isinstance(val, float) else (str(val) if val is not None else default)

    return {
        "user_id":            str(user_id),
        "movement_age":       _f("movement_age"),
        "bio_age":            _f("bio_age"),
        "movement_age_delta": _f("movement_age_delta"),
        "cadence":            _f("cadence"),
        "avg_speed":          _f("avg_speed"),
        "stride_length":      _f("stride_length"),
        "symmetry_score":     getattr(snapshot, "symmetry_score", 0.0),
        "stability_score":    getattr(snapshot, "stability_score", 0.0),
        "hip_rotation_rom":   _f("hip_rotation_rom"),
        "ankle_pushoff_proxy":_f("ankle_pushoff_proxy"),
        "vertical_oscillation":_f("vertical_oscillation"),
        "stride_time_cv":     _f("stride_time_cv"),
        "trunk_sway_rms":     _f("trunk_sway_rms"),
        "stance_phase_pct":   _f("stance_phase_pct"),
        "double_support_pct": _f("double_support_pct"),
        "anomaly_score":      _f("anomaly_score", "0.000"),
        "is_anomaly":         str(getattr(snapshot, "is_anomaly", False)),
        "trend_direction":    trend_direction or "unknown",
    }


async def _call_gemini(ctx: dict, audience: Literal["patient", "doctor"]) -> str:
    from app.core.config import settings
    import google.generativeai as genai

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not configured")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=_PATIENT_SYSTEM if audience == "patient" else _DOCTOR_SYSTEM,
    )

    prompt_template = _PATIENT_PROMPT if audience == "patient" else _DOCTOR_PROMPT
    prompt = prompt_template.format(**ctx)

    response = await model.generate_content_async(prompt)
    return response.text.strip()


def _fallback_message(audience: Literal["patient", "doctor"], ctx: dict) -> str:
    if audience == "patient":
        return (
            f"Your session is complete! Your movement age is {ctx['movement_age']} years "
            f"with a cadence of {ctx['cadence']} steps/min. "
            "Keep up your walking sessions for continued improvement."
        )
    return (
        f"Session metrics processed. Movement age: {ctx['movement_age']} yrs. "
        f"Cadence: {ctx['cadence']} spm. "
        f"Anomaly detected: {ctx['is_anomaly']} (score: {ctx['anomaly_score']}). "
        "Manual review recommended if anomaly is flagged."
    )


async def _cache_get(key: str) -> str | None:
    try:
        from app.core.redis import redis_client
        raw = await redis_client.get(key)
        if raw:
            return raw.decode() if isinstance(raw, bytes) else raw
    except Exception as e:
        logger.warning("Gemini cache GET failed: %s", e)
    return None


async def _cache_set(key: str, value: str) -> None:
    try:
        from app.core.redis import redis_client
        await redis_client.set(key, value, ex=CACHE_TTL)
    except Exception as e:
        logger.warning("Gemini cache SET failed: %s", e)
