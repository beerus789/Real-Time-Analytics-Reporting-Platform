from datetime import UTC, datetime
from uuid import UUID

from httpx import AsyncClient

from app.db.session import get_db_session
from app.services.ingestion import IngestionService
from tests.helpers import create_api_key, signup


async def _normalize_latest_raw_event(app, raw_event_id: str) -> None:
    async for session in app.dependency_overrides[get_db_session]():
        await IngestionService(session).normalize_raw_event(UUID(raw_event_id))


async def test_false_negative_valid_api_key_ingests_and_dashboard_reads_data(
    client: AsyncClient,
) -> None:
    token, _profile = await signup(client)
    api_key = await create_api_key(client, token)
    ingest = await client.post(
        "/api/v1/ingest/event",
        headers={"X-API-Key": api_key},
        json={
            "event_name": "checkout_completed",
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": "user-1",
            "properties": {"plan": "pro"},
        },
    )
    assert ingest.status_code == 202, ingest.text
    await _normalize_latest_raw_event(client.app, ingest.json()["raw_event_ids"][0])

    dashboard = await client.post(
        "/api/v1/dashboards",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Revenue", "auto_refresh_seconds": 60},
    )
    assert dashboard.status_code == 201, dashboard.text
    widget = await client.post(
        f"/api/v1/dashboards/{dashboard.json()['id']}/widgets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Completed checkouts",
            "kind": "kpi",
            "query": {
                "aggregate": "count",
                "event_name": "checkout_completed",
                "time_bucket": None,
                "filters": [],
            },
            "layout": {"x": 0, "y": 0, "w": 4, "h": 3},
        },
    )
    assert widget.status_code == 201, widget.text
    data = await client.get(
        f"/api/v1/dashboards/widgets/{widget.json()['id']}/data",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert data.status_code == 200, data.text
    assert data.json()["rows"][0]["value"] == 1


async def test_false_positive_revoked_api_key_is_rejected(client: AsyncClient) -> None:
    token, _profile = await signup(client)
    api_key = await create_api_key(client, token)
    keys = await client.get("/api/v1/api-keys", headers={"Authorization": f"Bearer {token}"})
    key_id = keys.json()[0]["id"]
    revoked = await client.delete(
        f"/api/v1/api-keys/{key_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert revoked.status_code == 200

    response = await client.post(
        "/api/v1/ingest/event",
        headers={"X-API-Key": api_key},
        json={
            "event_name": "page_view",
            "timestamp": datetime.now(UTC).isoformat(),
            "properties": {},
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_failed"


async def test_csv_partial_failure_keeps_valid_rows(client: AsyncClient) -> None:
    token, _profile = await signup(client)
    api_key = await create_api_key(client, token)
    csv_content = (
        "event_name,timestamp,user_id,properties\n"
        f"page_view,{datetime.now(UTC).isoformat()},u1,\"{{\"\"path\"\":\"\"/\"\"}}\"\n"
        "broken-date,not-a-date,u2,{}\n"
    )
    response = await client.post(
        "/api/v1/ingest/csv",
        headers={"X-API-Key": api_key},
        files={"file": ("events.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 202, response.text
    body = response.json()
    assert body["accepted"] == 1
    assert body["rejected"] == 1
    assert body["errors"]


async def test_org_isolation_cross_tenant_dashboard_access_rejected(client: AsyncClient) -> None:
    first_token, _profile = await signup(client, email="owner1@example.com", org="Org One")
    second_token, _profile = await signup(client, email="owner2@example.com", org="Org Two")
    dashboard = await client.post(
        "/api/v1/dashboards",
        headers={"Authorization": f"Bearer {first_token}"},
        json={"name": "Private", "auto_refresh_seconds": 60},
    )
    assert dashboard.status_code == 201

    response = await client.get(
        f"/api/v1/dashboards/{dashboard.json()['id']}",
        headers={"Authorization": f"Bearer {second_token}"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_public_share_read_only_and_authenticated_write_required(client: AsyncClient) -> None:
    token, _profile = await signup(client)
    dashboard = await client.post(
        "/api/v1/dashboards",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Shared", "auto_refresh_seconds": 30},
    )
    shared = await client.post(
        f"/api/v1/dashboards/{dashboard.json()['id']}/share",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert shared.status_code == 200, shared.text

    public = await client.get(f"/api/v1/public/dashboards/{shared.json()['share_token']}")
    assert public.status_code == 200, public.text

    write_attempt = await client.patch(
        f"/api/v1/dashboards/{dashboard.json()['id']}",
        json={"name": "Hijack"},
    )
    assert write_attempt.status_code == 401
