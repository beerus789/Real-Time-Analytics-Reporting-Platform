from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, get_current_context, require_roles
from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.models.enums import Role
from app.schemas.common import MessageResponse
from app.schemas.dashboard import (
    DashboardCreateRequest,
    DashboardDetailResponse,
    DashboardResponse,
    DashboardUpdateRequest,
    ShareResponse,
    WidgetCreateRequest,
    WidgetDataResponse,
    WidgetResponse,
    WidgetUpdateRequest,
)
from app.services.dashboards import DashboardService

router = APIRouter()
public_router = APIRouter()


@router.get("", response_model=list[DashboardResponse])
async def list_dashboards(
    context: AuthContext = Depends(get_current_context),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> list[DashboardResponse]:
    return await DashboardService(session, settings).list(context.organization_id)


@router.post("", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    payload: DashboardCreateRequest,
    context: AuthContext = Depends(require_roles(Role.OWNER, Role.ADMIN, Role.ANALYST)),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> DashboardResponse:
    return await DashboardService(session, settings).create(
        organization_id=context.organization_id,
        user_id=context.user_id,
        payload=payload,
    )


@router.get("/{dashboard_id}", response_model=DashboardDetailResponse)
async def get_dashboard(
    dashboard_id: UUID,
    context: AuthContext = Depends(get_current_context),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> DashboardDetailResponse:
    return await DashboardService(session, settings).get(
        organization_id=context.organization_id,
        dashboard_id=dashboard_id,
    )


@router.patch("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: UUID,
    payload: DashboardUpdateRequest,
    context: AuthContext = Depends(require_roles(Role.OWNER, Role.ADMIN, Role.ANALYST)),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> DashboardResponse:
    return await DashboardService(session, settings).update(
        organization_id=context.organization_id,
        dashboard_id=dashboard_id,
        payload=payload,
    )


@router.delete("/{dashboard_id}", response_model=MessageResponse)
async def delete_dashboard(
    dashboard_id: UUID,
    context: AuthContext = Depends(require_roles(Role.OWNER, Role.ADMIN)),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    await DashboardService(session, settings).delete(
        organization_id=context.organization_id,
        dashboard_id=dashboard_id,
    )
    return MessageResponse(message="Dashboard deleted.")


@router.post(
    "/{dashboard_id}/widgets",
    response_model=WidgetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_widget(
    dashboard_id: UUID,
    payload: WidgetCreateRequest,
    context: AuthContext = Depends(require_roles(Role.OWNER, Role.ADMIN, Role.ANALYST)),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> WidgetResponse:
    return await DashboardService(session, settings).add_widget(
        organization_id=context.organization_id,
        dashboard_id=dashboard_id,
        payload=payload,
    )


@router.patch("/widgets/{widget_id}", response_model=WidgetResponse)
async def update_widget(
    widget_id: UUID,
    payload: WidgetUpdateRequest,
    context: AuthContext = Depends(require_roles(Role.OWNER, Role.ADMIN, Role.ANALYST)),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> WidgetResponse:
    return await DashboardService(session, settings).update_widget(
        organization_id=context.organization_id,
        widget_id=widget_id,
        payload=payload,
    )


@router.delete("/widgets/{widget_id}", response_model=MessageResponse)
async def delete_widget(
    widget_id: UUID,
    context: AuthContext = Depends(require_roles(Role.OWNER, Role.ADMIN, Role.ANALYST)),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    await DashboardService(session, settings).delete_widget(
        organization_id=context.organization_id,
        widget_id=widget_id,
    )
    return MessageResponse(message="Widget deleted.")


@router.get("/widgets/{widget_id}/data", response_model=WidgetDataResponse)
async def widget_data(
    widget_id: UUID,
    context: AuthContext = Depends(get_current_context),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> WidgetDataResponse:
    return await DashboardService(session, settings).widget_data(
        organization_id=context.organization_id,
        widget_id=widget_id,
    )


@router.post("/{dashboard_id}/share", response_model=ShareResponse)
async def share_dashboard(
    dashboard_id: UUID,
    context: AuthContext = Depends(require_roles(Role.OWNER, Role.ADMIN, Role.ANALYST)),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ShareResponse:
    return await DashboardService(session, settings).share(
        organization_id=context.organization_id,
        dashboard_id=dashboard_id,
    )


@public_router.get("/dashboards/{share_token}", response_model=DashboardDetailResponse)
async def public_dashboard(
    share_token: str,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> DashboardDetailResponse:
    return await DashboardService(session, settings).get_public(share_token)


@public_router.get(
    "/dashboards/{share_token}/widgets/{widget_id}/data",
    response_model=WidgetDataResponse,
)
async def public_widget_data(
    share_token: str,
    widget_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> WidgetDataResponse:
    return await DashboardService(session, settings).public_widget_data(
        share_token=share_token,
        widget_id=widget_id,
    )
