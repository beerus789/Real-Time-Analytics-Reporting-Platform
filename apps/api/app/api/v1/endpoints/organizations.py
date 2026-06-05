from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, get_current_context, require_roles
from app.db.session import get_db_session
from app.models.enums import Role
from app.schemas.auth import InviteAcceptRequest
from app.schemas.common import MessageResponse
from app.schemas.organization import (
    DevOutboxMessage,
    InviteCreateRequest,
    InviteResponse,
    MembershipResponse,
)
from app.services.organizations import OrganizationService

router = APIRouter()


@router.get("/members", response_model=list[MembershipResponse])
async def list_members(
    context: AuthContext = Depends(get_current_context),
    session: AsyncSession = Depends(get_db_session),
) -> list[MembershipResponse]:
    return await OrganizationService(session).list_members(context.organization_id)


@router.post(
    "/invites",
    response_model=InviteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invite(
    payload: InviteCreateRequest,
    context: AuthContext = Depends(require_roles(Role.OWNER, Role.ADMIN)),
    session: AsyncSession = Depends(get_db_session),
) -> InviteResponse:
    invite, _token = await OrganizationService(session).create_invite(
        organization_id=context.organization_id,
        invited_by_id=context.user_id,
        payload=payload,
    )
    return invite


@router.get("/invites", response_model=list[InviteResponse])
async def list_invites(
    context: AuthContext = Depends(require_roles(Role.OWNER, Role.ADMIN)),
    session: AsyncSession = Depends(get_db_session),
) -> list[InviteResponse]:
    return await OrganizationService(session).list_invites(context.organization_id)


@router.get("/dev-outbox", response_model=list[DevOutboxMessage])
async def dev_outbox(
    context: AuthContext = Depends(require_roles(Role.OWNER, Role.ADMIN)),
    session: AsyncSession = Depends(get_db_session),
) -> list[DevOutboxMessage]:
    return await OrganizationService(session).list_dev_outbox(context.organization_id)


@router.post("/invites/accept", response_model=MessageResponse)
async def accept_invite(
    payload: InviteAcceptRequest,
    session: AsyncSession = Depends(get_db_session),
) -> MessageResponse:
    await OrganizationService(session).accept_invite(payload)
    return MessageResponse(message="Invite accepted.")

