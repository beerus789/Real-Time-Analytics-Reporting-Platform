from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from uuid import UUID

from fastapi import Cookie, Depends, Header, Response
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import AuthenticationError, RateLimitError
from app.core.permissions import assert_role
from app.core.security import decode_access_token
from app.db.session import get_db_session
from app.models.enums import Role
from app.repositories.organizations import OrganizationRepository
from app.services.api_keys import ApiKeyService


@dataclass(frozen=True)
class AuthContext:
    user_id: UUID
    organization_id: UUID
    role: Role


@dataclass(frozen=True)
class ApiKeyContext:
    api_key_id: UUID
    organization_id: UUID


async def get_current_context(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AuthContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthenticationError("Missing bearer token.")
    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(settings, token)
    context = AuthContext(
        user_id=UUID(str(payload["sub"])),
        organization_id=UUID(str(payload["org"])),
        role=Role(str(payload["role"])),
    )
    membership = await OrganizationRepository(session).get_membership(
        organization_id=context.organization_id,
        user_id=context.user_id,
    )
    if not membership or membership.role != context.role:
        raise AuthenticationError("Organization membership is no longer valid.")
    return context


def require_roles(*roles: Role) -> Callable[[AuthContext], Awaitable[AuthContext]]:
    async def dependency(context: AuthContext = Depends(get_current_context)) -> AuthContext:
        assert_role(context.role, set(roles))
        return context

    return dependency


async def get_refresh_cookie(refresh_token: str | None = Cookie(default=None)) -> str | None:
    return refresh_token


def set_refresh_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
        path=settings.refresh_cookie_path,
    )


def clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key="refresh_token",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
        path=settings.refresh_cookie_path,
    )


async def get_api_key_context(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ApiKeyContext:
    if not x_api_key:
        raise AuthenticationError("Missing X-API-Key header.")
    api_key = await ApiKeyService(session, settings).authenticate(x_api_key)
    return ApiKeyContext(api_key_id=api_key.id, organization_id=api_key.organization_id)


async def enforce_ingestion_rate_limit(
    api_context: ApiKeyContext = Depends(get_api_key_context),
    settings: Settings = Depends(get_settings),
) -> None:
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    key = f"rate:ingest:{api_context.organization_id}"
    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, 60)
    await redis.aclose()
    if current > settings.ingestion_rate_limit_per_minute:
        raise RateLimitError()
