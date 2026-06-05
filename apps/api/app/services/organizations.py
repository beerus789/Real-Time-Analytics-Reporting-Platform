from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.core.security import hash_password, hash_token
from app.models.organization import Invitation, OutboxMessage
from app.models.user import User
from app.repositories.organizations import OrganizationRepository
from app.repositories.users import UserRepository
from app.schemas.auth import InviteAcceptRequest
from app.schemas.organization import (
    DevOutboxMessage,
    InviteCreateRequest,
    InviteResponse,
    MembershipResponse,
)


class OrganizationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.organizations = OrganizationRepository(session)
        self.users = UserRepository(session)

    async def list_members(self, organization_id: UUID) -> list[MembershipResponse]:
        rows = await self.organizations.list_members(organization_id)
        return [
            MembershipResponse(
                id=membership.id,
                user_id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=membership.role,
            )
            for membership, user in rows
        ]

    async def create_invite(
        self,
        *,
        organization_id: UUID,
        invited_by_id: UUID,
        payload: InviteCreateRequest,
    ) -> tuple[InviteResponse, str]:
        existing_user = await self.users.get_by_email(payload.email)
        if existing_user:
            membership = await self.organizations.get_membership(
                organization_id=organization_id,
                user_id=existing_user.id,
            )
            if membership:
                raise ConflictError("This user is already a member.", code="member_exists")

        token = token_urlsafe(32)
        invitation = Invitation(
            organization_id=organization_id,
            email=payload.email.lower(),
            role=payload.role,
            token_hash=hash_token(token),
            expires_at=datetime.now(UTC) + timedelta(days=7),
            invited_by_id=invited_by_id,
        )
        outbox = OutboxMessage(
            organization_id=organization_id,
            recipient_email=payload.email.lower(),
            subject="You're invited to Pulseboard Analytics",
            body=f"Use this local invite token to join: {token}",
            payload={"token": token, "role": payload.role.value},
        )
        self.organizations.add_invite(invitation)
        self.organizations.add_outbox_message(outbox)
        await self.session.commit()
        return InviteResponse.model_validate(invitation), token

    async def list_invites(self, organization_id: UUID) -> list[InviteResponse]:
        invites = await self.organizations.list_invites(organization_id)
        return [InviteResponse.model_validate(item) for item in invites]

    async def list_dev_outbox(self, organization_id: UUID) -> list[DevOutboxMessage]:
        return [
            DevOutboxMessage.model_validate(item)
            for item in await self.organizations.list_outbox(organization_id)
        ]

    async def accept_invite(self, payload: InviteAcceptRequest) -> None:
        invitation = await self.organizations.find_active_invite_by_hash(hash_token(payload.token))
        if not invitation:
            raise NotFoundError("Invite token is invalid, expired, or already accepted.")

        user = await self.users.get_by_email(invitation.email)
        if user:
            membership = await self.organizations.get_membership(
                organization_id=invitation.organization_id,
                user_id=user.id,
            )
            if membership:
                raise ConflictError("This invite has already been accepted.")
        else:
            user = User(
                email=invitation.email,
                full_name=payload.full_name,
                password_hash=hash_password(payload.password),
            )
            self.users.add(user)
            await self.session.flush()

        self.organizations.add_membership(invitation.organization_id, user.id, invitation.role)
        invitation.accepted_at = datetime.now(UTC)
        self.session.add(invitation)
        await self.session.commit()
