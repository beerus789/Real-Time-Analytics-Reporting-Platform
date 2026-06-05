from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey


class ApiKeyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_org(self, organization_id: UUID) -> list[ApiKey]:
        result = await self.session.execute(
            select(ApiKey)
            .where(ApiKey.organization_id == organization_id)
            .order_by(ApiKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_for_org(self, *, organization_id: UUID, api_key_id: UUID) -> ApiKey | None:
        result = await self.session.execute(
            select(ApiKey).where(ApiKey.id == api_key_id, ApiKey.organization_id == organization_id)
        )
        return result.scalar_one_or_none()

    async def get_active_by_hash(self, key_hash: str) -> ApiKey | None:
        result = await self.session.execute(
            select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.revoked_at.is_(None))
        )
        return result.scalar_one_or_none()

    def add(self, api_key: ApiKey) -> None:
        self.session.add(api_key)

    async def mark_used(self, api_key: ApiKey) -> None:
        api_key.last_used_at = datetime.now(UTC)
        self.session.add(api_key)

