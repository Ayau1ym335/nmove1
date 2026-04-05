# backend/celery_app.py
from celery import Celery
from app.core.config import settings

celery = Celery("nmove")

celery.conf.update(
    broker_url=settings.REDIS_URL,
    result_backend=settings.REDIS_URL,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.tasks.process_session.process_session": {"queue": "gait_processing"},
        "app.tasks.process_session.close_and_process": {"queue": "gait_processing"},
    },
    result_expires=3600,
    task_soft_time_limit=60,
    task_time_limit=90,
)

celery.autodiscover_tasks(["app.tasks"])

app = celery
