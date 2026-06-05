import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://analytics:analytics@postgres:5432/analytics")
os.environ.setdefault(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://analytics:analytics@postgres:5432/analytics_test",
)

from app.api import deps as api_deps  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db_session  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
async def session_factory() -> AsyncGenerator[async_sessionmaker, None]:
    await ensure_test_database(os.environ["TEST_DATABASE_URL"])
    engine = create_async_engine(os.environ["TEST_DATABASE_URL"], pool_pre_ping=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def ensure_test_database(database_url: str) -> None:
    url = make_url(database_url)
    if not url.database:
        return
    maintenance_url = url.set(database="postgres")
    engine = create_async_engine(
        maintenance_url.render_as_string(hide_password=False),
        isolation_level="AUTOCOMMIT",
    )
    async with engine.connect() as connection:
        exists = await connection.scalar(
            text("select 1 from pg_database where datname = :database_name"),
            {"database_name": url.database},
        )
        if not exists:
            safe_database = url.database.replace('"', '""')
            await connection.execute(text(f'create database "{safe_database}"'))
    await engine.dispose()


@pytest.fixture
async def client(session_factory, monkeypatch) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def override_session():
        async with session_factory() as session:
            yield session

    async def no_rate_limit():
        return None

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[api_deps.enforce_ingestion_rate_limit] = no_rate_limit

    from app.tasks import ingestion as ingestion_tasks

    monkeypatch.setattr(ingestion_tasks.normalize_raw_event, "delay", lambda raw_id: None)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as test_client:
        test_client.app = app
        yield test_client
