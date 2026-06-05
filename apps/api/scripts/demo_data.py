import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.security import hash_password, hash_token
from app.db.session import AsyncSessionFactory
from app.models.api_key import ApiKey
from app.models.dashboard import Dashboard, Widget
from app.models.enums import DashboardVisibility, Role, SourceType, WidgetKind
from app.models.event import Event
from app.models.organization import Invitation, Membership, Organization, OutboxMessage
from app.models.user import User
from app.repositories.organizations import OrganizationRepository
from app.repositories.users import UserRepository

OWNER_EMAIL = "owner@example.com"
OWNER_PASSWORD = "Password123!"
DEMO_BATCH = "platform-demo-v1"
DEMO_API_KEY = "pa_demo_local_ingest_key_2026"
DEMO_INVITE_TOKEN = "demo-local-viewer-invite-token"
DEMO_SHARE_TOKEN = "demo-growth-overview"


async def ensure_owner_workspace(session: AsyncSession) -> tuple[Organization, User]:
    users = UserRepository(session)
    organizations = OrganizationRepository(session)
    owner = await users.get_by_email(OWNER_EMAIL)
    if owner:
        membership = await organizations.get_first_membership(owner.id)
        if membership:
            organization = await organizations.get(membership.organization_id)
            if organization:
                return organization, owner

    organization = await organizations.get_by_slug("acme-analytics")
    if not organization:
        organization = Organization(name="Acme Analytics", slug="acme-analytics")
        session.add(organization)

    if not owner:
        owner = User(
            email=OWNER_EMAIL,
            full_name="Acme Owner",
            password_hash=hash_password(OWNER_PASSWORD),
        )
        session.add(owner)

    await session.flush()
    membership = await organizations.get_membership(
        organization_id=organization.id,
        user_id=owner.id,
    )
    if not membership:
        session.add(Membership(organization_id=organization.id, user_id=owner.id, role=Role.OWNER))
    await session.flush()
    return organization, owner


async def ensure_role_member(
    session: AsyncSession,
    *,
    organization_id,
    email: str,
    full_name: str,
    role: Role,
) -> None:
    users = UserRepository(session)
    organizations = OrganizationRepository(session)
    user = await users.get_by_email(email)
    if not user:
        user = User(email=email, full_name=full_name, password_hash=hash_password(OWNER_PASSWORD))
        session.add(user)
        await session.flush()

    membership = await organizations.get_membership(
        organization_id=organization_id,
        user_id=user.id,
    )
    if not membership:
        session.add(Membership(organization_id=organization_id, user_id=user.id, role=role))


async def ensure_team_data(session: AsyncSession, organization: Organization, owner: User) -> None:
    await ensure_role_member(
        session,
        organization_id=organization.id,
        email="admin@example.com",
        full_name="Acme Admin",
        role=Role.ADMIN,
    )
    await ensure_role_member(
        session,
        organization_id=organization.id,
        email="analyst@example.com",
        full_name="Acme Analyst",
        role=Role.ANALYST,
    )
    await ensure_role_member(
        session,
        organization_id=organization.id,
        email="viewer@example.com",
        full_name="Acme Viewer",
        role=Role.VIEWER,
    )

    token_hash = hash_token(DEMO_INVITE_TOKEN)
    result = await session.execute(select(Invitation).where(Invitation.token_hash == token_hash))
    invitation = result.scalar_one_or_none()
    if not invitation:
        invitation = Invitation(
            organization_id=organization.id,
            email="pending.viewer@example.com",
            role=Role.VIEWER,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(days=14),
            invited_by_id=owner.id,
        )
        outbox = OutboxMessage(
            organization_id=organization.id,
            recipient_email="pending.viewer@example.com",
            subject="You're invited to Pulseboard Analytics",
            body=f"Use this local invite token to join: {DEMO_INVITE_TOKEN}",
            payload={"token": DEMO_INVITE_TOKEN, "role": Role.VIEWER.value},
        )
        session.add_all([invitation, outbox])


async def ensure_demo_api_key(
    session: AsyncSession,
    organization: Organization,
    owner: User,
) -> None:
    result = await session.execute(
        select(ApiKey).where(ApiKey.key_hash == hash_token(DEMO_API_KEY))
    )
    api_key = result.scalar_one_or_none()
    if api_key:
        api_key.revoked_at = None
        session.add(api_key)
        return

    session.add(
        ApiKey(
            organization_id=organization.id,
            name="Demo ingestion key",
            prefix=DEMO_API_KEY[:12],
            key_hash=hash_token(DEMO_API_KEY),
            created_by_id=owner.id,
        )
    )


def build_demo_events(organization: Organization) -> list[Event]:
    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    paths = ["/", "/pricing", "/docs", "/dashboard", "/settings"]
    plans = ["starter", "team", "enterprise"]
    countries = ["US", "IN", "GB", "DE", "BR"]
    campaigns = ["organic", "paid-search", "partner", "newsletter"]
    devices = ["desktop", "mobile", "tablet"]
    events: list[Event] = []

    for day in range(30):
        day_at = now - timedelta(days=day)
        for index in range(12 + day % 5):
            events.append(
                Event(
                    organization_id=organization.id,
                    event_name="page_view",
                    occurred_at=day_at - timedelta(minutes=index * 7),
                    user_id=f"demo-user-{(day + index) % 18}",
                    source_type=SourceType.API,
                    properties={
                        "demo_batch": DEMO_BATCH,
                        "path": paths[index % len(paths)],
                        "device": devices[(day + index) % len(devices)],
                        "campaign": campaigns[(day + index) % len(campaigns)],
                    },
                )
            )

        for index in range(3 + day % 3):
            plan = plans[(day + index) % len(plans)]
            campaign = campaigns[(day + index) % len(campaigns)]
            user_id = f"signup-user-{day}-{index}"
            events.append(
                Event(
                    organization_id=organization.id,
                    event_name="signup_completed",
                    occurred_at=day_at - timedelta(hours=2, minutes=index * 9),
                    user_id=user_id,
                    source_type=SourceType.API,
                    properties={
                        "demo_batch": DEMO_BATCH,
                        "plan": plan,
                        "campaign": campaign,
                        "country": countries[(day + index) % len(countries)],
                    },
                )
            )
            if index % 2 == 0:
                events.append(
                    Event(
                        organization_id=organization.id,
                        event_name="checkout_started",
                        occurred_at=day_at - timedelta(hours=3, minutes=index * 11),
                        user_id=user_id,
                        source_type=SourceType.API,
                        properties={
                            "demo_batch": DEMO_BATCH,
                            "plan": plan,
                            "campaign": campaign,
                        },
                    )
                )

        purchase_count = 1 + int(day % 4 == 0)
        for index in range(purchase_count):
            events.append(
                Event(
                    organization_id=organization.id,
                    event_name="purchase_completed",
                    occurred_at=day_at - timedelta(hours=4, minutes=index * 13),
                    user_id=f"customer-{day}-{index}",
                    source_type=SourceType.API,
                    properties={
                        "demo_batch": DEMO_BATCH,
                        "plan": plans[(day + index + 1) % len(plans)],
                        "country": countries[(day + index) % len(countries)],
                        "amount": 49 + ((day + index) % 5) * 25,
                    },
                )
            )

        if day % 3 == 0:
            events.append(
                Event(
                    organization_id=organization.id,
                    event_name="invite_accepted",
                    occurred_at=day_at - timedelta(hours=5),
                    user_id=f"team-user-{day}",
                    source_type=SourceType.API,
                    properties={"demo_batch": DEMO_BATCH, "role": Role.ANALYST.value},
                )
            )

    return events


async def ensure_demo_events(session: AsyncSession, organization: Organization) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(Event)
        .where(
            Event.organization_id == organization.id,
            Event.properties["demo_batch"].astext == DEMO_BATCH,
        )
    )
    existing_count = int(result.scalar_one())
    if existing_count:
        return existing_count

    events = build_demo_events(organization)
    session.add_all(events)
    return len(events)


async def ensure_demo_dashboard(
    session: AsyncSession,
    organization: Organization,
    owner: User,
) -> Dashboard:
    result = await session.execute(
        select(Dashboard)
        .where(
            Dashboard.organization_id == organization.id,
            Dashboard.name == "Demo Growth Analytics",
            Dashboard.deleted_at.is_(None),
        )
        .options(selectinload(Dashboard.widgets))
    )
    dashboard = result.scalar_one_or_none()
    existing_widgets: set[str] = set()
    if not dashboard:
        dashboard = Dashboard(
            organization_id=organization.id,
            created_by_id=owner.id,
            name="Demo Growth Analytics",
            description="Richer demo dashboard with every must-have widget type.",
            auto_refresh_seconds=30,
            visibility=DashboardVisibility.PUBLIC,
            share_token=DEMO_SHARE_TOKEN,
        )
        session.add(dashboard)
        await session.flush()
    else:
        existing_widgets = {widget.title for widget in dashboard.widgets}
        dashboard.auto_refresh_seconds = 30
        dashboard.visibility = DashboardVisibility.PUBLIC
        dashboard.share_token = dashboard.share_token or DEMO_SHARE_TOKEN
        session.add(dashboard)

    specs = [
        (
            "Total demo events",
            WidgetKind.KPI,
            {
                "aggregate": "count",
                "event_name": None,
                "group_by": None,
                "time_bucket": None,
                "filters": [{"field": "property:demo_batch", "op": "eq", "value": DEMO_BATCH}],
            },
            {"x": 0, "y": 0, "w": 3, "h": 3},
        ),
        (
            "Page views by day",
            WidgetKind.LINE,
            {
                "aggregate": "count",
                "event_name": "page_view",
                "group_by": None,
                "time_bucket": "day",
                "filters": [{"field": "property:demo_batch", "op": "eq", "value": DEMO_BATCH}],
            },
            {"x": 3, "y": 0, "w": 6, "h": 4},
        ),
        (
            "Signups by plan",
            WidgetKind.BAR,
            {
                "aggregate": "count",
                "event_name": "signup_completed",
                "group_by": "property:plan",
                "time_bucket": None,
                "filters": [{"field": "property:demo_batch", "op": "eq", "value": DEMO_BATCH}],
            },
            {"x": 9, "y": 0, "w": 3, "h": 4},
        ),
        (
            "Purchases by country",
            WidgetKind.PIE,
            {
                "aggregate": "count",
                "event_name": "purchase_completed",
                "group_by": "property:country",
                "time_bucket": None,
                "filters": [{"field": "property:demo_batch", "op": "eq", "value": DEMO_BATCH}],
            },
            {"x": 0, "y": 4, "w": 5, "h": 4},
        ),
        (
            "Campaign breakdown",
            WidgetKind.TABLE,
            {
                "aggregate": "unique_users",
                "event_name": "page_view",
                "group_by": "property:campaign",
                "time_bucket": None,
                "filters": [{"field": "property:demo_batch", "op": "eq", "value": DEMO_BATCH}],
            },
            {"x": 5, "y": 4, "w": 7, "h": 4},
        ),
    ]

    for title, kind, query, layout in specs:
        if title not in existing_widgets:
            session.add(
                Widget(
                    dashboard_id=dashboard.id,
                    title=title,
                    kind=kind,
                    query=query,
                    layout=layout,
                )
            )

    return dashboard


async def load_demo_data() -> None:
    settings = get_settings()
    async with AsyncSessionFactory() as session:
        organization, owner = await ensure_owner_workspace(session)
        await ensure_team_data(session, organization, owner)
        await ensure_demo_api_key(session, organization, owner)
        event_count = await ensure_demo_events(session, organization)
        dashboard = await ensure_demo_dashboard(session, organization, owner)
        await session.commit()
        print(f"Demo data ready for {settings.app_name}")
        print(f"Workspace: {organization.name} ({organization.slug})")
        print(f"Login: {OWNER_EMAIL} / {OWNER_PASSWORD}")
        print(f"Demo API key: {DEMO_API_KEY}")
        print(f"Demo event rows: {event_count}")
        print(f"Public dashboard token: {dashboard.share_token}")


if __name__ == "__main__":
    asyncio.run(load_demo_data())
