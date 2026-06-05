import asyncio
from uuid import UUID

from app.core.celery_app import celery_app
from app.db.session import AsyncSessionFactory
from app.services.ingestion import IngestionService


@celery_app.task(
    name="app.tasks.ingestion.normalize_raw_event",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def normalize_raw_event(raw_event_id: str) -> None:
    asyncio.run(_normalize(raw_event_id))


async def _normalize(raw_event_id: str) -> None:
    async with AsyncSessionFactory() as session:
        await IngestionService(session).normalize_raw_event(UUID(raw_event_id))

