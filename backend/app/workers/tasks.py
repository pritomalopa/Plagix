import logging
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.workers.tasks.diagnostic_ping")
def diagnostic_ping(self, message: str = "ping") -> dict:
    """Safe diagnostic worker task to verify Celery worker execution."""
    logger.info("Executing diagnostic task with message: %s", message)
    return {
        "status": "success",
        "message": f"pong: {message}",
        "task_id": self.request.id,
    }
