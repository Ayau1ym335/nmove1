import logging
from datetime import datetime
from uuid import UUID

from celery_app import celery
from app.tasks.base_task import NMoveBaseTask
from app.db.sync_session import get_sync_db
from app.models.gait_session import GaitSession
from app.models.gait_reading import GaitReading
from app.models.metrics_snapshot import MetricsSnapshot
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

            readings = db.query(GaitReading)\
                .filter(GaitReading.gait_session_id == UUID(session_id))\
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

            metrics = compute_gait_metrics(readings)
            movement_age = compute_movement_age(metrics, session)
            interpretation = compute_interpretation(metrics, movement_age)

            snapshot = MetricsSnapshot(
                gait_session_id=UUID(session_id),
                cadence=metrics["cadence"],
                symmetry_score=metrics["symmetry_score"],
                stability_score=metrics["stability_score"],
                movement_age=movement_age["movement_age"],
                bio_age=movement_age["bio_age"],
                movement_age_delta=movement_age["delta"],
                interpretation_status=interpretation["status"],
            )
            db.add(snapshot)
            db.flush()   

            for ex in interpretation["exercises"]:
                exercise = Exercise(
                    metrics_snapshot_id=snapshot.id,
                    title=ex["title"],
                    description=ex["description"],
                    difficulty=ex["difficulty"],
                    duration_minutes=ex.get("duration_minutes", None),
                )
                db.add(exercise)
            db.commit()
            
        sync_update_session_status(session_id, "done", reading_count=len(readings))

        return {
            "status": "processed",
            "session_id": session_id,
            "readings_processed": len(readings),
            "cadence": metrics["cadence"],
            "symmetry_score": metrics["symmetry_score"],
            "stability_score": metrics["stability_score"],
            "movement_age": movement_age["movement_age"],
            "interpretation_status": interpretation["status"],
            "exercises_created": len(interpretation["exercises"]),
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
        logger.exception(f"close_and_process failed for {session_id}: {exc}")
        raise self.retry(exc=exc, countdown=10 * (self.request.retries + 1))
