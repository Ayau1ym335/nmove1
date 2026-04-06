import logging
from datetime import datetime, timedelta
from celery_app import celery
from app.tasks.base_task import NMoveBaseTask
from app.db.sync_session import get_sync_db

from app.reports.builder import assemble_report_data
from app.reports.charts import build_movement_age_svg, build_radar_svg, build_symmetry_svg, build_cadence_svg
from app.reports.medical_text import generate_clinical_text
from app.reports.renderer import render_pdf
from app.services.minio_service import upload_report, generate_presigned_url

logger = logging.getLogger("nmove.tasks")

@celery.task(
    bind=True,
    base=NMoveBaseTask,
    name="app.tasks.generate_report.generate_report",
    max_retries=2,
    queue="gait_processing",
    soft_time_limit=120,
    time_limit=180,
)
def generate_report(
    self,
    patient_id: str,
    doctor_id: str,
    days: int,
) -> dict:
    try:
        # Load core properties
        with get_sync_db() as db:
            data = assemble_report_data(db, patient_id, doctor_id, days)

        # Static Chart Builder
        data.charts_svg = {
            "movement_age":    build_movement_age_svg(data),
            "radar":           build_radar_svg(data),
            "symmetry":        build_symmetry_svg(data),
            "cadence":         build_cadence_svg(data),
        }

        # Deterministic text computation
        data.clinical_text = generate_clinical_text(data)

        # Print layout binding
        pdf_bytes = render_pdf(data)

        # Minio persistence
        uid_pat = data.patient.get("id", patient_id)
        uid_doc = data.doctor.get("id", doctor_id)
        object_name = upload_report(pdf_bytes, uid_pat, uid_doc, datetime.utcnow())

        # Final signature
        url = generate_presigned_url(object_name, expires_hours=48)

        return {
            "status": "done",
            "object_name": object_name,
            "url": url,
            "expires_at": (datetime.utcnow() + timedelta(hours=48)).isoformat(),
            "page_count": 6,
        }

    except Exception as exc:
        logger.exception(f"generate_report failed for patient={patient_id}, doctor={doctor_id}: {exc}")
        raise self.retry(exc=exc, countdown=30 * (self.request.retries + 1))
