from datetime import UTC, datetime
from secrets import token_urlsafe
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import AuthenticationError, ConflictError, NotFoundError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.enums import Role
from app.models.organization import Organization
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.organizations import OrganizationRepository
from app.repositories.users import UserRepository
from app.schemas.auth import SignupRequest, TokenResponse, UserProfile


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.users = UserRepository(session)
        self.organizations = OrganizationRepository(session)

    async def signup(self, payload: SignupRequest) -> tuple[TokenResponse, str]:
        existing_user = await self.users.get_by_email(payload.email)
        if existing_user:
            raise ConflictError("A user with this email already exists.", code="user_exists")

        slug = await self._unique_org_slug(payload.organization_name)
        user = User(
            email=payload.email.lower(),
            full_name=payload.full_name,
            password_hash=hash_password(payload.password),
        )
        organization = Organization(name=payload.organization_name, slug=slug)
        self.users.add(user)
        self.organizations.add_organization(organization)
        await self.session.flush()
        self.organizations.add_membership(organization.id, user.id, Role.OWNER)
        await self.session.commit()

        return await self._issue_tokens(user_id=user.id)

    async def signin(self, *, email: str, password: str) -> tuple[TokenResponse, str]:
        user = await self.users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError("Email or password is incorrect.")
        if not user.is_active:
            raise AuthenticationError("This user account is disabled.")
        return await self._issue_tokens(user_id=user.id)

    async def refresh(self, refresh_token: str) -> tuple[TokenResponse, str]:
        payload = decode_refresh_token(self.settings, refresh_token)
        jti_hash = hash_token(str(payload["jti"]))
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.jti_hash == jti_hash)
        )
        stored = result.scalar_one_or_none()
        if not stored or stored.revoked_at or stored.expires_at <= datetime.now(UTC):
            raise AuthenticationError("Refresh token has been revoked.")
        stored.revoked_at = datetime.now(UTC)
        self.session.add(stored)
        return await self._issue_tokens(user_id=UUID(str(payload["sub"])))

    async def logout(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return
        payload = decode_refresh_token(self.settings, refresh_token)
        jti_hash = hash_token(str(payload["jti"]))
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.jti_hash == jti_hash)
        )
        stored = result.scalar_one_or_none()
        if stored:
            stored.revoked_at = datetime.now(UTC)
            self.session.add(stored)
            await self.session.commit()

    async def profile(self, user_id: UUID, organization_id: UUID) -> UserProfile:
        user = await self.users.get(user_id)
        membership = await self.organizations.get_membership(
            organization_id=organization_id,
            user_id=user_id,
        )
        organization = await self.organizations.get(organization_id)
        if not user or not membership or not organization:
            raise NotFoundError("Current organization context was not found.")
        return UserProfile(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            organization_id=organization.id,
            organization_name=organization.name,
            role=membership.role,
        )

    async def _issue_tokens(self, user_id: UUID) -> tuple[TokenResponse, str]:
        membership = await self.organizations.get_first_membership(user_id)
        if not membership:
            raise AuthenticationError("User is not a member of any organization.")
        token, jti, expires_at = create_refresh_token(settings=self.settings, user_id=str(user_id))
        refresh = RefreshToken(user_id=user_id, jti_hash=hash_token(jti), expires_at=expires_at)
        self.session.add(refresh)
        access = create_access_token(
            settings=self.settings,
            user_id=str(user_id),
            organization_id=str(membership.organization_id),
            role=membership.role.value,
        )
        await self.session.commit()
        return (
            TokenResponse(
                access_token=access,
                expires_in=self.settings.access_token_ttl_minutes * 60,
            ),
            token,
        )

    async def _unique_org_slug(self, name: str) -> str:
        base = "".join(ch if ch.isalnum() else "-" for ch in name.lower()).strip("-")
        base = "-".join(part for part in base.split("-") if part) or "organization"
        slug = base
        while await self.organizations.get_by_slug(slug):
            slug = f"{base}-{token_urlsafe(4).lower()}"
        return slug
