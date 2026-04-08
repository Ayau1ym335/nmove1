import os
from datetime import datetime, timedelta
from uuid import UUID
from minio import Minio
from minio.error import S3Error
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

BUCKET_NAME = "nmove-reports"

def _get_client() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD,
        secure=settings.MINIO_SECURE,
    )

def ensure_bucket_exists() -> None:
    client = _get_client()
    try:
        found = client.bucket_exists(BUCKET_NAME)
        if not found:
            client.make_bucket(BUCKET_NAME)
            logger.info(f"Created MinIO bucket '{BUCKET_NAME}'")
    except S3Error as e:
        logger.error(f"MinIO bucket creation failed: {e}")

def upload_report(
    pdf_bytes: bytes,
    patient_id: UUID,
    doctor_id: UUID,
    generated_at: datetime,
) -> str:
    import io
    client = _get_client()
    
    # reports/patient_id/year/month/iso_doctor_id.pdf
    year = generated_at.strftime("%Y")
    month = generated_at.strftime("%m")
    iso_time = generated_at.strftime("%Y%m%dT%H%M%S")
    object_name = f"reports/{patient_id}/{year}/{month}/{iso_time}_{doctor_id}.pdf"
    
    stream = io.BytesIO(pdf_bytes)
    
    client.put_object(
        bucket_name=BUCKET_NAME,
        object_name=object_name,
        data=stream,
        length=len(pdf_bytes),
        content_type="application/pdf",
        metadata={
            "patient_id": str(patient_id),
            "doctor_id": str(doctor_id),
            "generated_at": generated_at.isoformat()
        }
    )
    return object_name

def generate_presigned_url(
    object_name: str,
    expires_hours: int = 48,
) -> str:
    client = _get_client()
    url = client.presigned_get_object(
        bucket_name=BUCKET_NAME,
        object_name=object_name,
        expires=timedelta(hours=expires_hours),
    )
    return url

from app.schemas.report import ReportListItem

def list_patient_reports(
    patient_id: UUID,
) -> list[ReportListItem]:
    client = _get_client()
    prefix = f"reports/{patient_id}/"
    results = []
    try:
        objects = client.list_objects(BUCKET_NAME, prefix=prefix, recursive=True)
        
        for obj in objects:
            if obj.is_dir or obj.object_name is None:
                continue
            
            # Fresh presigned URL
            url = generate_presigned_url(obj.object_name, 48)
            
            dt = obj.last_modified if obj.last_modified else datetime.utcnow()
            if dt.tzinfo is not None:
                 dt = dt.replace(tzinfo=None)
                 
            results.append(ReportListItem(
                object_name=obj.object_name,
                generated_at=dt,
                size_bytes=int(obj.size or 0),
                url=url,
                expires_at=dt + timedelta(hours=48),
                days_window=None
            ))
            
        results.sort(key=lambda r: r.generated_at, reverse=True)
        return results
    except S3Error as e:
        logger.error(f"S3Error listing reports for patient={patient_id}: {e}")
        return []
