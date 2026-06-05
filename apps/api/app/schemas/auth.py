from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import Role
from app.schemas.common import ORMModel


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(min_length=2, max_length=160)
    organization_name: str = Field(min_length=2, max_length=160)


class SigninRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserProfile(ORMModel):
    id: UUID
    email: EmailStr
    full_name: str
    organization_id: UUID
    organization_name: str
    role: Role


class InviteAcceptRequest(BaseModel):
    token: str = Field(min_length=16)
    full_name: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=10, max_length=128)

