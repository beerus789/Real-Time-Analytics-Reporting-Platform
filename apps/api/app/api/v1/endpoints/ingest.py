from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ApiKeyContext, enforce_ingestion_rate_limit, get_api_key_context
from app.db.session import get_db_session
from app.models.enums import SourceType
from app.schemas.ingest import (
    BatchEventRequest,
    CsvUploadResponse,
    EventPayload,
    IngestAcceptedResponse,
)
from app.services.ingestion import IngestionService

router = APIRouter()


@router.post(
    "/event",
    response_model=IngestAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(enforce_ingestion_rate_limit)],
)
async def ingest_event(
    payload: EventPayload,
    context: ApiKeyContext = Depends(get_api_key_context),
    session: AsyncSession = Depends(get_db_session),
) -> IngestAcceptedResponse:
    return await IngestionService(session).accept_events(
        organization_id=context.organization_id,
        api_key_id=context.api_key_id,
        payloads=[payload],
        source_type=SourceType.API,
    )


@router.post(
    "/batch",
    response_model=IngestAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(enforce_ingestion_rate_limit)],
)
async def ingest_batch(
    payload: BatchEventRequest,
    context: ApiKeyContext = Depends(get_api_key_context),
    session: AsyncSession = Depends(get_db_session),
) -> IngestAcceptedResponse:
    return await IngestionService(session).accept_events(
        organization_id=context.organization_id,
        api_key_id=context.api_key_id,
        payloads=payload.events,
        source_type=SourceType.API,
    )


@router.post(
    "/csv",
    response_model=CsvUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(enforce_ingestion_rate_limit)],
)
async def ingest_csv(
    file: UploadFile = File(...),
    context: ApiKeyContext = Depends(get_api_key_context),
    session: AsyncSession = Depends(get_db_session),
) -> CsvUploadResponse:
    return await IngestionService(session).accept_csv(
        organization_id=context.organization_id,
        api_key_id=context.api_key_id,
        filename=file.filename or "events.csv",
        content=await file.read(),
    )

