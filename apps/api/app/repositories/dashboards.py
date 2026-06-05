from secrets import token_urlsafe
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dashboard import Dashboard, Widget
from app.models.enums import DashboardVisibility


class DashboardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_org(self, organization_id: UUID) -> list[Dashboard]:
        result = await self.session.execute(
            select(Dashboard)
            .where(Dashboard.organization_id == organization_id, Dashboard.deleted_at.is_(None))
            .order_by(Dashboard.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_for_org(self, *, organization_id: UUID, dashboard_id: UUID) -> Dashboard | None:
        result = await self.session.execute(
            select(Dashboard)
            .where(
                Dashboard.id == dashboard_id,
                Dashboard.organization_id == organization_id,
                Dashboard.deleted_at.is_(None),
            )
            .options(selectinload(Dashboard.widgets))
        )
        return result.scalar_one_or_none()

    async def get_public(self, share_token: str) -> Dashboard | None:
        result = await self.session.execute(
            select(Dashboard)
            .where(
                Dashboard.share_token == share_token,
                Dashboard.visibility == DashboardVisibility.PUBLIC,
                Dashboard.deleted_at.is_(None),
            )
            .options(selectinload(Dashboard.widgets))
        )
        return result.scalar_one_or_none()

    async def get_widget_for_org(self, *, organization_id: UUID, widget_id: UUID) -> Widget | None:
        result = await self.session.execute(
            select(Widget)
            .join(Dashboard, Dashboard.id == Widget.dashboard_id)
            .where(
                Widget.id == widget_id,
                Dashboard.organization_id == organization_id,
                Dashboard.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    def add_dashboard(self, dashboard: Dashboard) -> None:
        self.session.add(dashboard)

    def add_widget(self, widget: Widget) -> None:
        self.session.add(widget)

    def ensure_public_share(self, dashboard: Dashboard) -> str:
        if not dashboard.share_token:
            dashboard.share_token = token_urlsafe(24)
        dashboard.visibility = DashboardVisibility.PUBLIC
        self.session.add(dashboard)
        return dashboard.share_token

