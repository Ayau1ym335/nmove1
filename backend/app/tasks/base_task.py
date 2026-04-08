# backend/app/tasks/base_task.py
import logging
import celery

logger = logging.getLogger("nmove.tasks")

class NMoveBaseTask(celery.Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {self.name}[{task_id}] failed: {exc}", exc_info=einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.warning(f"Task {self.name}[{task_id}] retrying due to: {exc}")

    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {self.name}[{task_id}] completed successfully")
