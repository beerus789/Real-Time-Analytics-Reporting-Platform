from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    AuthContext,
    clear_refresh_cookie,
    get_current_context,
    get_refresh_cookie,
    set_refresh_cookie,
)
from app.core.config import Settings, get_settings
from app.core.errors import AuthenticationError
from app.db.session import get_db_session
from app.schemas.auth import SigninRequest, SignupRequest, TokenResponse, UserProfile
from app.schemas.common import MessageResponse
from app.services.auth import AuthService

router = APIRouter()


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    token_response, refresh = await AuthService(session, settings).signup(payload)
    set_refresh_cookie(response, refresh, settings)
    return token_response


@router.post("/signin", response_model=TokenResponse)
async def signin(
    payload: SigninRequest,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    token_response, refresh = await AuthService(session, settings).signin(
        email=payload.email,
        password=payload.password,
    )
    set_refresh_cookie(response, refresh, settings)
    return token_response


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    refresh_token: str | None = Depends(get_refresh_cookie),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    if not refresh_token:
        raise AuthenticationError("Refresh token cookie is missing.")
    token_response, refresh_value = await AuthService(session, settings).refresh(refresh_token)
    set_refresh_cookie(response, refresh_value, settings)
    return token_response


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    refresh_token: str | None = Depends(get_refresh_cookie),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    await AuthService(session, settings).logout(refresh_token)
    clear_refresh_cookie(response, settings)
    return MessageResponse(message="Logged out.")


@router.get("/me", response_model=UserProfile)
async def me(
    context: AuthContext = Depends(get_current_context),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> UserProfile:
    return await AuthService(session, settings).profile(
        user_id=context.user_id,
        organization_id=context.organization_id,
    )

