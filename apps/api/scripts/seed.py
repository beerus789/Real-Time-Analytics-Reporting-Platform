import asyncio
from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import AsyncSessionFactory
from app.models.dashboard import Dashboard, Widget
from app.models.enums import Role, SourceType, WidgetKind
from app.models.event import Event
from app.models.organization import Membership, Organization
from app.models.user import User
from app.repositories.users import UserRepository


async def seed() -> None:
    settings = get_settings()
    async with AsyncSessionFactory() as session:
        existing = await UserRepository(session).get_by_email("owner@example.com")
        if existing:
            print("Seed user already exists: owner@example.com")
            return

        organization = Organization(name="Acme Analytics", slug="acme-analytics")
        user = User(
            email="owner@example.com",
            full_name="Acme Owner",
            password_hash=hash_password("Password123!"),
        )
        session.add_all([organization, user])
        await session.flush()
        session.add(Membership(organization_id=organization.id, user_id=user.id, role=Role.OWNER))

        now = datetime.now(UTC)
        for day in range(7):
            session.add(
                Event(
                    organization_id=organization.id,
                    event_name="page_view",
                    occurred_at=now - timedelta(days=day),
                    user_id=f"user-{day % 3}",
                    source_type=SourceType.API,
                    properties={"path": "/pricing", "browser": "Chrome"},
                )
            )
            session.add(
                Event(
                    organization_id=organization.id,
                    event_name="signup_completed",
                    occurred_at=now - timedelta(days=day, hours=2),
                    user_id=f"user-{day}",
                    source_type=SourceType.API,
                    properties={"plan": "team"},
                )
            )

        dashboard = Dashboard(
            organization_id=organization.id,
            created_by_id=user.id,
            name="Growth Overview",
            description="Starter analytics dashboard seeded for local verification.",
            auto_refresh_seconds=60,
        )
        session.add(dashboard)
        await session.flush()
        session.add_all(
            [
                Widget(
                    dashboard_id=dashboard.id,
                    title="Page views by day",
                    kind=WidgetKind.LINE,
                    query={
                        "aggregate": "count",
                        "event_name": "page_view",
                        "group_by": None,
                        "time_bucket": "day",
                        "filters": [],
                    },
                    layout={"x": 0, "y": 0, "w": 8, "h": 4},
                ),
                Widget(
                    dashboard_id=dashboard.id,
                    title="Signups",
                    kind=WidgetKind.KPI,
                    query={
                        "aggregate": "count",
                        "event_name": "signup_completed",
                        "group_by": None,
                        "time_bucket": None,
                        "filters": [],
                    },
                    layout={"x": 8, "y": 0, "w": 4, "h": 4},
                ),
            ]
        )
        await session.commit()
        print(f"Seeded {settings.app_name}: owner@example.com / Password123!")


if __name__ == "__main__":
    asyncio.run(seed())

