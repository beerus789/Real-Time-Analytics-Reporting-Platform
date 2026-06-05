from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.enums import IngestStatus, SourceType


class EventPayload(BaseModel):
    event_name: str = Field(min_length=1, max_length=160)
    timestamp: datetime
    user_id: str | None = Field(default=None, max_length=180)
    properties: dict[str, Any] = Field(default_factory=dict)

    @field_validator("properties")
    @classmethod
    def properties_must_be_object(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("properties must be an object")
        return value


class BatchEventRequest(BaseModel):
    events: list[EventPayload] = Field(min_length=1, max_length=500)


class IngestAcceptedResponse(BaseModel):
    accepted: int
    rejected: int
    raw_event_ids: list[UUID]
    errors: list[dict[str, Any]] = Field(default_factory=list)


class RawEventResponse(BaseModel):
    id: UUID
    status: IngestStatus
    source_type: SourceType


class CsvUploadResponse(IngestAcceptedResponse):
    filename: str

