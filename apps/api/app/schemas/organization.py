from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import Role
from app.schemas.common import ORMModel


class OrganizationResponse(ORMModel):
    id: UUID
    name: str
    slug: str


class MembershipResponse(ORMModel):
    id: UUID
    user_id: UUID
    email: EmailStr
    full_name: str
    role: Role


class InviteCreateRequest(BaseModel):
    email: EmailStr
    role: Role


class InviteResponse(ORMModel):
    id: UUID
    email: EmailStr
    role: Role
    expires_at: datetime
    accepted_at: datetime | None


class DevOutboxMessage(ORMModel):
    id: UUID
    recipient_email: EmailStr
    subject: str
    body: str
    payload: dict = Field(default_factory=dict)
    created_at: datetime

