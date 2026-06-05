from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=140)


class ApiKeyCreateResponse(BaseModel):
    id: UUID
    name: str
    prefix: str
    key: str
    created_at: datetime


class ApiKeyResponse(ORMModel):
    id: UUID
    name: str
    prefix: str
    created_at: datetime
    revoked_at: datetime | None
    last_used_at: datetime | None

