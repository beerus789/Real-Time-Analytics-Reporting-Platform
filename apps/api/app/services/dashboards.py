from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import NotFoundError
from app.models.dashboard import Dashboard, Widget
from app.repositories.dashboards import DashboardRepository
from app.repositories.events import EventRepository
from app.schemas.dashboard import (
    DashboardCreateRequest,
    DashboardDetailResponse,
    DashboardResponse,
    DashboardUpdateRequest,
    ShareResponse,
    WidgetCreateRequest,
    WidgetDataResponse,
    WidgetQuery,
    WidgetResponse,
    WidgetUpdateRequest,
)


class DashboardService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.dashboards = DashboardRepository(session)
        self.events = EventRepository(session)

    async def list(self, organization_id: UUID) -> list[DashboardResponse]:
        dashboards = await self.dashboards.list_for_org(organization_id)
        return [DashboardResponse.model_validate(item) for item in dashboards]

    async def create(
        self,
        *,
        organization_id: UUID,
        user_id: UUID,
        payload: DashboardCreateRequest,
    ) -> DashboardResponse:
        dashboard = Dashboard(
            organization_id=organization_id,
            created_by_id=user_id,
            name=payload.name,
            description=payload.description,
            auto_refresh_seconds=payload.auto_refresh_seconds,
        )
        self.dashboards.add_dashboard(dashboard)
        await self.session.commit()
        await self.session.refresh(dashboard)
        return DashboardResponse.model_validate(dashboard)

    async def get(self, *, organization_id: UUID, dashboard_id: UUID) -> DashboardDetailResponse:
        dashboard = await self.dashboards.get_for_org(
            organization_id=organization_id,
            dashboard_id=dashboard_id,
        )
        if not dashboard:
            raise NotFoundError("Dashboard was not found.")
        return DashboardDetailResponse.model_validate(dashboard)

    async def update(
        self,
        *,
        organization_id: UUID,
        dashboard_id: UUID,
        payload: DashboardUpdateRequest,
    ) -> DashboardResponse:
        dashboard = await self.dashboards.get_for_org(
            organization_id=organization_id,
            dashboard_id=dashboard_id,
        )
        if not dashboard:
            raise NotFoundError("Dashboard was not found.")
        if payload.name is not None:
            dashboard.name = payload.name
        if payload.description is not None:
            dashboard.description = payload.description
        if payload.auto_refresh_seconds is not None:
            dashboard.auto_refresh_seconds = payload.auto_refresh_seconds
        self.session.add(dashboard)
        await self.session.commit()
        await self.session.refresh(dashboard)
        return DashboardResponse.model_validate(dashboard)

    async def delete(self, *, organization_id: UUID, dashboard_id: UUID) -> None:
        dashboard = await self.dashboards.get_for_org(
            organization_id=organization_id,
            dashboard_id=dashboard_id,
        )
        if not dashboard:
            raise NotFoundError("Dashboard was not found.")
        dashboard.deleted_at = datetime.now(UTC)
        self.session.add(dashboard)
        await self.session.commit()

    async def add_widget(
        self,
        *,
        organization_id: UUID,
        dashboard_id: UUID,
        payload: WidgetCreateRequest,
    ) -> WidgetResponse:
        dashboard = await self.dashboards.get_for_org(
            organization_id=organization_id,
            dashboard_id=dashboard_id,
        )
        if not dashboard:
            raise NotFoundError("Dashboard was not found.")
        widget = Widget(
            dashboard_id=dashboard.id,
            title=payload.title,
            kind=payload.kind,
            query=payload.query.model_dump(mode="json"),
            layout=payload.layout.model_dump(),
        )
        self.dashboards.add_widget(widget)
        await self.session.commit()
        await self.session.refresh(widget)
        return WidgetResponse.model_validate(widget)

    async def update_widget(
        self,
        *,
        organization_id: UUID,
        widget_id: UUID,
        payload: WidgetUpdateRequest,
    ) -> WidgetResponse:
        widget = await self.dashboards.get_widget_for_org(
            organization_id=organization_id,
            widget_id=widget_id,
        )
        if not widget:
            raise NotFoundError("Widget was not found.")
        if payload.title is not None:
            widget.title = payload.title
        if payload.kind is not None:
            widget.kind = payload.kind
        if payload.query is not None:
            widget.query = payload.query.model_dump(mode="json")
        if payload.layout is not None:
            widget.layout = payload.layout.model_dump()
        self.session.add(widget)
        await self.session.commit()
        await self.session.refresh(widget)
        return WidgetResponse.model_validate(widget)

    async def delete_widget(self, *, organization_id: UUID, widget_id: UUID) -> None:
        widget = await self.dashboards.get_widget_for_org(
            organization_id=organization_id,
            widget_id=widget_id,
        )
        if not widget:
            raise NotFoundError("Widget was not found.")
        await self.session.delete(widget)
        await self.session.commit()

    async def share(
        self,
        *,
        organization_id: UUID,
        dashboard_id: UUID,
        public_base_url: str | None = None,
    ) -> ShareResponse:
        dashboard = await self.dashboards.get_for_org(
            organization_id=organization_id,
            dashboard_id=dashboard_id,
        )
        if not dashboard:
            raise NotFoundError("Dashboard was not found.")
        token = self.dashboards.ensure_public_share(dashboard)
        await self.session.commit()
        base_url = str(
            public_base_url or self.settings.public_share_base_url or self.settings.frontend_origin
        ).rstrip("/")
        return ShareResponse(
            dashboard_id=dashboard.id,
            share_token=token,
            public_url=f"{base_url}/share/{token}",
        )

    async def get_public(self, share_token: str) -> DashboardDetailResponse:
        dashboard = await self.dashboards.get_public(share_token)
        if not dashboard:
            raise NotFoundError("Shared dashboard was not found.")
        return DashboardDetailResponse.model_validate(dashboard)

    async def public_widget_data(self, *, share_token: str, widget_id: UUID) -> WidgetDataResponse:
        dashboard = await self.dashboards.get_public(share_token)
        if not dashboard:
            raise NotFoundError("Shared dashboard was not found.")
        widget = next((item for item in dashboard.widgets if item.id == widget_id), None)
        if not widget:
            raise NotFoundError("Widget was not found.")
        spec = WidgetQuery.model_validate(widget.query)
        if spec.from_ts is None:
            spec.from_ts = datetime.now(UTC) - timedelta(days=7)
        rows = await self.events.query_widget(organization_id=dashboard.organization_id, spec=spec)
        return WidgetDataResponse(widget_id=widget.id, kind=widget.kind, rows=rows)

    async def widget_data(
        self,
        *,
        organization_id: UUID,
        widget_id: UUID,
    ) -> WidgetDataResponse:
        widget = await self.dashboards.get_widget_for_org(
            organization_id=organization_id,
            widget_id=widget_id,
        )
        if not widget:
            raise NotFoundError("Widget was not found.")
        spec = WidgetQuery.model_validate(widget.query)
        if spec.from_ts is None:
            spec.from_ts = datetime.now(UTC) - timedelta(days=7)
        rows = await self.events.query_widget(organization_id=organization_id, spec=spec)
        return WidgetDataResponse(widget_id=widget.id, kind=widget.kind, rows=rows)
