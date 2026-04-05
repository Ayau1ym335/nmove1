# backend/worker.py
# Usage: python worker.py
# Or via docker CMD: celery -A celery_app worker ...
import logging
from celery_app import celery  # noqa: F401 — triggers task autodiscover

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

if __name__ == "__main__":
    celery.worker_main(
        argv=[
            "worker",
            "--loglevel=info",
            "--queues=gait_processing",
            "--concurrency=2",
        ]
    )
