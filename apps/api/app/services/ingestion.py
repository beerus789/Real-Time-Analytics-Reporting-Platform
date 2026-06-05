import csv
import json
from io import StringIO
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import IngestStatus, SourceType
from app.repositories.events import EventRepository
from app.schemas.ingest import CsvUploadResponse, EventPayload, IngestAcceptedResponse


class IngestionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.events = EventRepository(session)

    async def accept_events(
        self,
        *,
        organization_id: UUID,
        api_key_id: UUID | None,
        payloads: list[EventPayload],
        source_type: SourceType,
        enqueue: bool = True,
    ) -> IngestAcceptedResponse:
        raw_ids: list[UUID] = []
        for payload in payloads:
            raw = self.events.add_raw(
                organization_id=organization_id,
                api_key_id=api_key_id,
                payload=payload.model_dump(mode="json"),
                source_type=source_type,
            )
            await self.session.flush()
            raw_ids.append(raw.id)
        await self.session.commit()

        if enqueue and raw_ids:
            from app.tasks.ingestion import normalize_raw_event

            for raw_id in raw_ids:
                normalize_raw_event.delay(str(raw_id))

        return IngestAcceptedResponse(accepted=len(raw_ids), rejected=0, raw_event_ids=raw_ids)

    async def accept_csv(
        self,
        *,
        organization_id: UUID,
        api_key_id: UUID | None,
        filename: str,
        content: bytes,
    ) -> CsvUploadResponse:
        decoded = content.decode("utf-8-sig")
        reader = csv.DictReader(StringIO(decoded))
        payloads: list[EventPayload] = []
        errors: list[dict] = []

        required = {"event_name", "timestamp", "user_id", "properties"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            return CsvUploadResponse(
                filename=filename,
                accepted=0,
                rejected=0,
                raw_event_ids=[],
                errors=[{"row": 0, "message": f"Missing columns: {', '.join(sorted(missing))}"}],
            )

        for row_number, row in enumerate(reader, start=2):
            try:
                properties = json.loads(row.get("properties") or "{}")
                payloads.append(
                    EventPayload(
                        event_name=row.get("event_name") or "",
                        timestamp=row.get("timestamp"),
                        user_id=row.get("user_id") or None,
                        properties=properties,
                    )
                )
            except (ValidationError, json.JSONDecodeError) as exc:
                errors.append({"row": row_number, "message": str(exc)})

        accepted = await self.accept_events(
            organization_id=organization_id,
            api_key_id=api_key_id,
            payloads=payloads,
            source_type=SourceType.CSV,
        ) if payloads else IngestAcceptedResponse(accepted=0, rejected=0, raw_event_ids=[])

        return CsvUploadResponse(
            filename=filename,
            accepted=accepted.accepted,
            rejected=len(errors),
            raw_event_ids=accepted.raw_event_ids,
            errors=errors,
        )

    async def normalize_raw_event(self, raw_event_id: UUID) -> None:
        raw = await self.events.get_pending_raw(raw_event_id)
        if not raw:
            return
        try:
            payload = EventPayload.model_validate(raw.payload)
            self.events.add_event(
                organization_id=raw.organization_id,
                raw_event_id=raw.id,
                event_name=payload.event_name,
                occurred_at=payload.timestamp,
                user_id=payload.user_id,
                source_type=raw.source_type,
                properties=payload.properties,
            )
            raw.status = IngestStatus.PROCESSED
            raw.error_message = None
        except ValidationError as exc:
            raw.status = IngestStatus.FAILED
            raw.error_message = str(exc)
        self.session.add(raw)
        await self.session.commit()

