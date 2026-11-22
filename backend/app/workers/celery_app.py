from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "plagix_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.tasks",
        "app.workers.ingestion_tasks",
        "app.workers.similarity_tasks"
    ]
)

celery_app.conf.update(
    broker_url=settings.redis_url,
    result_backend=settings.redis_url,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_lost_wait=20.0,
    broker_connection_retry_on_startup=True,
)
