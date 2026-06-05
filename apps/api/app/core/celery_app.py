from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "analytics_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.ingestion"],
)

celery_app.conf.update(
    task_acks_late=True,
    task_default_retry_delay=10,
    task_routes={"app.tasks.ingestion.*": {"queue": "ingestion"}},
    worker_prefetch_multiplier=1,
)

