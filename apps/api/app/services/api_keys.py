from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import AuthenticationError, NotFoundError
from app.core.security import hash_token, make_api_key
from app.models.api_key import ApiKey
from app.repositories.api_keys import ApiKeyRepository
from app.schemas.api_key import ApiKeyCreateResponse, ApiKeyResponse


class ApiKeyService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.api_keys = ApiKeyRepository(session)

    async def create(
        self,
        *,
        organization_id: UUID,
        user_id: UUID,
        name: str,
    ) -> ApiKeyCreateResponse:
        key, prefix = make_api_key(self.settings)
        api_key = ApiKey(
            organization_id=organization_id,
            name=name,
            prefix=prefix,
            key_hash=hash_token(key),
            created_by_id=user_id,
        )
        self.api_keys.add(api_key)
        await self.session.commit()
        await self.session.refresh(api_key)
        return ApiKeyCreateResponse(
            id=api_key.id,
            name=api_key.name,
            prefix=api_key.prefix,
            key=key,
            created_at=api_key.created_at,
        )

    async def list(self, organization_id: UUID) -> list[ApiKeyResponse]:
        api_keys = await self.api_keys.list_for_org(organization_id)
        return [ApiKeyResponse.model_validate(item) for item in api_keys]

    async def revoke(self, *, organization_id: UUID, api_key_id: UUID) -> None:
        api_key = await self.api_keys.get_for_org(
            organization_id=organization_id,
            api_key_id=api_key_id,
        )
        if not api_key:
            raise NotFoundError("API key was not found.")
        api_key.revoked_at = datetime.now(UTC)
        self.session.add(api_key)
        await self.session.commit()

    async def rotate(self, *, organization_id: UUID, api_key_id: UUID) -> ApiKeyCreateResponse:
        api_key = await self.api_keys.get_for_org(
            organization_id=organization_id,
            api_key_id=api_key_id,
        )
        if not api_key:
            raise NotFoundError("API key was not found.")
        key, prefix = make_api_key(self.settings)
        api_key.prefix = prefix
        api_key.key_hash = hash_token(key)
        api_key.revoked_at = None
        self.session.add(api_key)
        await self.session.commit()
        await self.session.refresh(api_key)
        return ApiKeyCreateResponse(
            id=api_key.id,
            name=api_key.name,
            prefix=api_key.prefix,
            key=key,
            created_at=api_key.created_at,
        )

    async def authenticate(self, key: str) -> ApiKey:
        api_key = await self.api_keys.get_active_by_hash(hash_token(key))
        if not api_key:
            raise AuthenticationError("API key is invalid or revoked.")
        await self.api_keys.mark_used(api_key)
        await self.session.commit()
        return api_key
