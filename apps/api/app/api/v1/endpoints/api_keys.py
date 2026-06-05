from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, require_roles
from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.models.enums import Role
from app.schemas.api_key import ApiKeyCreateRequest, ApiKeyCreateResponse, ApiKeyResponse
from app.schemas.common import MessageResponse
from app.services.api_keys import ApiKeyService

router = APIRouter()


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    context: AuthContext = Depends(require_roles(Role.OWNER, Role.ADMIN, Role.ANALYST)),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> list[ApiKeyResponse]:
    return await ApiKeyService(session, settings).list(context.organization_id)


@router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: ApiKeyCreateRequest,
    context: AuthContext = Depends(require_roles(Role.OWNER, Role.ADMIN)),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ApiKeyCreateResponse:
    return await ApiKeyService(session, settings).create(
        organization_id=context.organization_id,
        user_id=context.user_id,
        name=payload.name,
    )


@router.post("/{api_key_id}/rotate", response_model=ApiKeyCreateResponse)
async def rotate_api_key(
    api_key_id: UUID,
    context: AuthContext = Depends(require_roles(Role.OWNER, Role.ADMIN)),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ApiKeyCreateResponse:
    return await ApiKeyService(session, settings).rotate(
        organization_id=context.organization_id,
        api_key_id=api_key_id,
    )


@router.delete("/{api_key_id}", response_model=MessageResponse)
async def revoke_api_key(
    api_key_id: UUID,
    context: AuthContext = Depends(require_roles(Role.OWNER, Role.ADMIN)),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    await ApiKeyService(session, settings).revoke(
        organization_id=context.organization_id,
        api_key_id=api_key_id,
    )
    return MessageResponse(message="API key revoked.")

