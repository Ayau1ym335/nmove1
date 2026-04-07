import logging
from datetime import datetime
from uuid import UUID

from celery_app import celery
from app.tasks.base_task import NMoveBaseTask
from app.db.sync_session import get_sync_db
from app.models.gait_session import GaitSession
from app.models.gait_reading import GaitReading
from app.models.metrics_snapshot import MetricsSnapshot
from app.models.user import User
from app.models.exercise import Exercise
from app.services.metrics_service import compute_gait_metrics
from app.services.movement_age_service import compute_movement_age
from app.services.interpretation_service import compute_interpretation
from app.services.session_service import sync_update_session_status

logger = logging.getLogger("nmove.tasks")

@celery.task(
    bind=True,
    base=NMoveBaseTask,
    name="app.tasks.process_session.process_session",
    max_retries=3,
    default_retry_delay=10,
    queue="gait_processing",
)
def process_session(self, session_id: str) -> dict:
    sync_update_session_status(session_id, "processing")
    
    try:
        with get_sync_db() as db:
            existing = db.query(MetricsSnapshot)\
                .filter(MetricsSnapshot.gait_session_id == UUID(session_id))\
                .first()
            if existing:
                logger.info(f"Snapshot already exists for session {session_id}, skipping")
                sync_update_session_status(session_id, "done")
                return {"status": "skipped", "reason": "already_processed"}

            session = db.query(GaitSession).filter(GaitSession.id == UUID(session_id)).first()
            if not session:
                logger.warning(f"Session {session_id} not found, skipping processing")
                return {"status": "skipped", "reason": "session_not_found"}

            filters = [GaitReading.gait_session_id == UUID(session_id)]
            if getattr(session, 'started_at', None):
                filters.append(GaitReading.time >= session.started_at)
            if getattr(session, 'ended_at', None):
                filters.append(GaitReading.time <= session.ended_at)

            readings = db.query(GaitReading)\
                .filter(*filters)\
                .order_by(GaitReading.time.asc())\
                .all()

            if len(readings) < 10:
                logger.info(f"Session {session_id} has only {len(readings)} readings — "
                            "skipping until more data arrives")
                sync_update_session_status(
                    session_id, "error", 
                    error_message="Insufficient readings (< 10) to process"
                )
                return {"status": "skipped", "reason": "insufficient_readings", "count": len(readings)}

            user = db.query(User).filter(User.id == session.user_id).first()
            bio_age = user.bio_age if user else None

            metrics = compute_gait_metrics(readings)
            movement_age_result = compute_movement_age(metrics, bio_age)
            interpretation = compute_interpretation(metrics, movement_age_result)

            # NOTE ON METRICS SNAPSHOT: `domain_scores` and `composite_score` do not exist on the table.
            # We are injecting the relevant movement_age mappings into existing stable DB columns without a migration.
            snapshot = MetricsSnapshot(
                gait_session_id=UUID(session_id),
                # ── Rhythm & Pace ────────────────────────────────────────────────
                cadence=metrics["cadence"],
                stride_length=metrics.get("stride_length"),
                step_count=metrics.get("step_count"),
                avg_speed=metrics.get("avg_speed"),
                # ── Joint Mechanics ───────────────────────────────────────────────
                hip_rotation_rom=metrics.get("hip_rotation_rom"),
                ankle_pushoff_proxy=metrics.get("ankle_pushoff_proxy"),
                vertical_oscillation=metrics.get("vertical_oscillation"),
                # ── Variability ─────────────────────────────────────────────────────────
                stride_time_cv=metrics.get("stride_time_cv"),
                trunk_sway_rms=metrics.get("trunk_sway_rms"),
                # ── Symmetry & Phases ──────────────────────────────────────────────
                symmetry_score=metrics["step_symmetry_ratio"],
                stance_phase_pct=metrics.get("stance_phase_pct"),
                double_support_pct=metrics.get("double_support_pct"),
                # ── Movement Age & Composite ──────────────────────────────────────────
                stability_score=movement_age_result["composite_score"],
                movement_age=movement_age_result["movement_age"],
                bio_age=movement_age_result["bio_age"],
                movement_age_delta=movement_age_result["delta"],
                interpretation_status=interpretation["status"],
            )
            db.add(snapshot)
            db.flush()   

            for ex in interpretation.get("exercises", []):
                exercise = Exercise(
                    metrics_snapshot_id=snapshot.id,
                    title=ex["title"],
                    description=ex["description"],
                    difficulty=ex["difficulty"],
                )
                db.add(exercise)
            db.commit()
            
        sync_update_session_status(session_id, "done", reading_count=len(readings))

        # ── ML Anomaly Scoring ────────────────────────────────────────────────────────────
        # Runs in a fresh DB context immediately after the snapshot is committed.
        # Updates anomaly_score + is_anomaly on the snapshot row.
        try:
            from app.ml.scorer import score_snapshot
            from app.db.sync_session import get_sync_db
            from app.models.metrics_snapshot import MetricsSnapshot as MS
            with get_sync_db() as score_db:
                fresh_snap = score_db.query(MS).filter(MS.id == snapshot.id).first()
                if fresh_snap:
                    a_score, a_flag = score_snapshot(fresh_snap, str(session.user_id))
                    if a_score is not None:
                        fresh_snap.anomaly_score = a_score
                        fresh_snap.is_anomaly    = a_flag
                        score_db.commit()
                        logger.info(
                            "Anomaly score set for session=%s: %.3f (anomaly=%s)",
                            session_id, a_score, a_flag,
                        )
        except Exception:
            logger.exception(
                "Anomaly scoring failed for session=%s (non-fatal)", session_id
            )

        # ── ML Training trigger ──────────────────────────────────────────────────────────
        # Runs after the snapshot is committed. A fresh DB context is used so
        # that ML failure never rolls back the main processing transaction.
        try:
            from app.ml.trainer import maybe_train_model
            from app.db.sync_session import get_sync_db
            with get_sync_db() as ml_db:
                maybe_train_model(str(session.user_id), ml_db)
        except Exception:
            logger.exception(
                "ML training trigger failed for session=%s (non-fatal)", session_id
            )

        try:
            from app.services.n8n_service import trigger_webhook_fire_and_forget
            trigger_webhook_fire_and_forget("session-complete", {
                "session_id": session_id,
                "movement_age": movement_age_result["movement_age"],
                "interpretation": interpretation["status"]
            })
        except Exception:
            pass

        return {
            "status": "processed",
            "session_id": session_id,
            "readings_processed": len(readings),
            "cadence": metrics["cadence"],
            "symmetry_score": metrics["step_symmetry_ratio"],
            "stability_score": movement_age_result["composite_score"],
            "movement_age": movement_age_result["movement_age"],
            "interpretation_status": interpretation["status"],
            "exercises_created": len(interpretation.get("exercises", [])),
        }
        
    except Exception as exc:
        sync_update_session_status(
            session_id, "error", 
            error_message=f"Processing failed: {str(exc)[:500]}"
        )
        logger.exception(f"process_session failed for {session_id}: {exc}")
        raise self.retry(exc=exc, countdown=10 * (self.request.retries + 1))


@celery.task(
    bind=True,
    base=NMoveBaseTask,
    name="app.tasks.process_session.close_and_process",
    max_retries=2,
    default_retry_delay=5,
    queue="gait_processing",
)
def close_and_process(self, session_id: str) -> dict:
    try:
        with get_sync_db() as db:
            session = db.query(GaitSession).filter(GaitSession.id == UUID(session_id)).first()
            if not session:
                return {"status": "skipped", "reason": "session_not_found"}

            if session.ended_at is not None:
                return {"status": "skipped", "reason": "already_closed"}

            session.ended_at = datetime.utcnow()
            duration = (session.ended_at - session.started_at.replace(tzinfo=None)).total_seconds()
            session.duration_seconds = duration
            db.commit()

            process_session.delay(session_id)
            return {
                "status": "closed_and_queued",
                "session_id": session_id,
                "duration_seconds": duration
            }
    except Exception as exc:
        from app.services.session_service import sync_update_session_status
        sync_update_session_status(
            session_id, "error", 
            error_message=f"close_and_process failed: {str(exc)[:500]}"
        )
        logger.exception(f"close_and_process failed for {session_id}: {exc}")
        raise self.retry(exc=exc, countdown=10 * (self.request.retries + 1))
