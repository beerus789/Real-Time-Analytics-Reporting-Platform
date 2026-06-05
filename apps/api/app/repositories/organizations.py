from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import Role
from app.models.organization import Invitation, Membership, Organization, OutboxMessage
from app.models.user import User


class OrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, organization_id: UUID) -> Organization | None:
        return await self.session.get(Organization, organization_id)

    async def get_by_slug(self, slug: str) -> Organization | None:
        result = await self.session.execute(select(Organization).where(Organization.slug == slug))
        return result.scalar_one_or_none()

    async def get_membership(self, *, organization_id: UUID, user_id: UUID) -> Membership | None:
        result = await self.session.execute(
            select(Membership).where(
                Membership.organization_id == organization_id,
                Membership.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_first_membership(self, user_id: UUID) -> Membership | None:
        result = await self.session.execute(
            select(Membership)
            .where(Membership.user_id == user_id)
            .options(selectinload(Membership.organization))
            .order_by(Membership.created_at.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_members(self, organization_id: UUID) -> list[tuple[Membership, User]]:
        result = await self.session.execute(
            select(Membership, User)
            .join(User, User.id == Membership.user_id)
            .where(Membership.organization_id == organization_id)
            .order_by(Membership.created_at.asc())
        )
        return list(result.all())

    async def list_invites(self, organization_id: UUID) -> list[Invitation]:
        result = await self.session.execute(
            select(Invitation)
            .where(Invitation.organization_id == organization_id)
            .order_by(Invitation.created_at.desc())
        )
        return list(result.scalars().all())

    async def find_active_invite_by_hash(self, token_hash: str) -> Invitation | None:
        now = datetime.now(UTC)
        result = await self.session.execute(
            select(Invitation).where(
                Invitation.token_hash == token_hash,
                Invitation.accepted_at.is_(None),
                Invitation.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    async def list_outbox(self, organization_id: UUID) -> list[OutboxMessage]:
        result = await self.session.execute(
            select(OutboxMessage)
            .where(OutboxMessage.organization_id == organization_id)
            .order_by(OutboxMessage.created_at.desc())
        )
        return list(result.scalars().all())

    def add_organization(self, organization: Organization) -> None:
        self.session.add(organization)

    def add_membership(self, organization_id: UUID, user_id: UUID, role: Role) -> Membership:
        membership = Membership(organization_id=organization_id, user_id=user_id, role=role)
        self.session.add(membership)
        return membership

    def add_invite(self, invitation: Invitation) -> None:
        self.session.add(invitation)

    def add_outbox_message(self, message: OutboxMessage) -> None:
        self.session.add(message)

