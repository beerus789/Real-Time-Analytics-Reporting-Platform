import asyncio
import csv
import json
import os
from datetime import UTC, datetime
from io import StringIO
from uuid import uuid4

import httpx

BASE_URL = os.getenv("SMOKE_BASE_URL", "http://localhost:8000/api/v1")
OWNER_EMAIL = "owner@example.com"
OWNER_PASSWORD = "Password123!"


class SmokeFailure(AssertionError):
    pass


async def request(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    *,
    expected: int | set[int],
    token: str | None = None,
    api_key: str | None = None,
    **kwargs,
) -> httpx.Response:
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if api_key:
        headers["X-API-Key"] = api_key

    response = await client.request(method, path, headers=headers, **kwargs)
    expected_statuses = {expected} if isinstance(expected, int) else expected
    if response.status_code not in expected_statuses:
        raise SmokeFailure(
            f"{method} {path} returned {response.status_code}, expected "
            f"{sorted(expected_statuses)}: {response.text}"
        )
    return response


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


async def wait_for_widget_rows(
    client: httpx.AsyncClient,
    *,
    token: str,
    widget_id: str,
    min_value: int,
) -> list[dict]:
    for _ in range(20):
        response = await request(
            client,
            "GET",
            f"/dashboards/widgets/{widget_id}/data",
            expected=200,
            token=token,
        )
        rows = response.json()["rows"]
        if rows and int(rows[0].get("value", 0)) >= min_value:
            return rows
        await asyncio.sleep(0.75)
    raise SmokeFailure(f"Widget {widget_id} did not receive normalized event rows in time.")


def csv_payload(event_name: str) -> bytes:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["event_name", "timestamp", "user_id", "properties"],
    )
    writer.writeheader()
    writer.writerow(
        {
            "event_name": event_name,
            "timestamp": utc_now(),
            "user_id": "csv-user",
            "properties": json.dumps({"plan": "team", "channel": "email"}),
        }
    )
    writer.writerow(
        {
            "event_name": "broken_csv_event",
            "timestamp": "not-a-date",
            "user_id": "csv-user",
            "properties": "{}",
        }
    )
    return output.getvalue().encode("utf-8")


async def run() -> None:
    nonce = uuid4().hex[:10]
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=20.0) as client:
        await request(client, "GET", "/health", expected=200)

        wrong_password = await request(
            client,
            "POST",
            "/auth/signin",
            expected=401,
            json={"email": OWNER_EMAIL, "password": "incorrect"},
        )
        assert wrong_password.json()["error"]["code"] == "authentication_failed"

        signin = await request(
            client,
            "POST",
            "/auth/signin",
            expected=200,
            json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD},
        )
        owner_token = signin.json()["access_token"]
        refreshed = await request(client, "POST", "/auth/refresh", expected=200)
        owner_token = refreshed.json()["access_token"]

        me = await request(client, "GET", "/auth/me", expected=200, token=owner_token)
        assert me.json()["role"] == "Owner"

        members = await request(
            client,
            "GET",
            "/organizations/members",
            expected=200,
            token=owner_token,
        )
        assert any(member["role"] == "Admin" for member in members.json())
        assert any(member["role"] == "Viewer" for member in members.json())

        invite_email = f"smoke-viewer-{nonce}@example.com"
        await request(
            client,
            "POST",
            "/organizations/invites",
            expected=201,
            token=owner_token,
            json={"email": invite_email, "role": "Viewer"},
        )
        outbox = await request(
            client,
            "GET",
            "/organizations/dev-outbox",
            expected=200,
            token=owner_token,
        )
        invite_token = next(
            item["payload"]["token"]
            for item in outbox.json()
            if item["recipient_email"] == invite_email
        )
        await request(
            client,
            "POST",
            "/organizations/invites/accept",
            expected=200,
            json={
                "token": invite_token,
                "full_name": "Smoke Viewer",
                "password": OWNER_PASSWORD,
            },
        )
        viewer_signin = await request(
            client,
            "POST",
            "/auth/signin",
            expected=200,
            json={"email": invite_email, "password": OWNER_PASSWORD},
        )
        viewer_token = viewer_signin.json()["access_token"]
        await request(
            client,
            "POST",
            "/api-keys",
            expected=403,
            token=viewer_token,
            json={"name": "Viewer should fail"},
        )

        active_key_response = await request(
            client,
            "POST",
            "/api-keys",
            expected=201,
            token=owner_token,
            json={"name": f"Smoke active {nonce}"},
        )
        active_key = active_key_response.json()["key"]
        await request(client, "GET", "/api-keys", expected=200, token=owner_token)

        revoked_key_response = await request(
            client,
            "POST",
            "/api-keys",
            expected=201,
            token=owner_token,
            json={"name": f"Smoke revoked {nonce}"},
        )
        revoked = revoked_key_response.json()
        await request(
            client,
            "DELETE",
            f"/api-keys/{revoked['id']}",
            expected=200,
            token=owner_token,
        )
        await request(
            client,
            "POST",
            "/ingest/event",
            expected=401,
            api_key=revoked["key"],
            json={
                "event_name": "revoked_key_should_fail",
                "timestamp": utc_now(),
                "user_id": "smoke",
                "properties": {},
            },
        )

        rotated_key_response = await request(
            client,
            "POST",
            f"/api-keys/{active_key_response.json()['id']}/rotate",
            expected=200,
            token=owner_token,
        )
        rotated_key = rotated_key_response.json()["key"]
        await request(
            client,
            "POST",
            "/ingest/event",
            expected=401,
            api_key=active_key,
            json={
                "event_name": "rotated_old_key_should_fail",
                "timestamp": utc_now(),
                "user_id": "smoke",
                "properties": {},
            },
        )

        event_name = f"smoke_single_{nonce}"
        batch_event = f"smoke_batch_{nonce}"
        csv_event = f"smoke_csv_{nonce}"
        await request(
            client,
            "POST",
            "/ingest/event",
            expected=202,
            api_key=rotated_key,
            json={
                "event_name": event_name,
                "timestamp": utc_now(),
                "user_id": "smoke-user",
                "properties": {"channel": "api", "plan": "enterprise"},
            },
        )
        await request(
            client,
            "POST",
            "/ingest/batch",
            expected=202,
            api_key=rotated_key,
            json={
                "events": [
                    {
                        "event_name": batch_event,
                        "timestamp": utc_now(),
                        "user_id": "batch-user-1",
                        "properties": {"channel": "product"},
                    },
                    {
                        "event_name": batch_event,
                        "timestamp": utc_now(),
                        "user_id": "batch-user-2",
                        "properties": {"channel": "email"},
                    },
                ]
            },
        )
        csv_response = await request(
            client,
            "POST",
            "/ingest/csv",
            expected=202,
            api_key=rotated_key,
            files={"file": ("smoke.csv", csv_payload(csv_event), "text/csv")},
        )
        assert csv_response.json()["accepted"] == 1
        assert csv_response.json()["rejected"] == 1

        dashboard_response = await request(
            client,
            "POST",
            "/dashboards",
            expected=201,
            token=owner_token,
            json={
                "name": f"Smoke Dashboard {nonce}",
                "description": "Created by live smoke test.",
                "auto_refresh_seconds": 30,
            },
        )
        dashboard_id = dashboard_response.json()["id"]

        widget_specs = [
            (
                "Smoke KPI",
                "kpi",
                {"aggregate": "count", "event_name": event_name, "time_bucket": None},
                {"x": 0, "y": 0, "w": 3, "h": 3},
            ),
            (
                "Smoke Line",
                "line",
                {"aggregate": "count", "event_name": batch_event, "time_bucket": "hour"},
                {"x": 3, "y": 0, "w": 5, "h": 3},
            ),
            (
                "Smoke Bar",
                "bar",
                {
                    "aggregate": "count",
                    "event_name": batch_event,
                    "group_by": "property:channel",
                    "time_bucket": None,
                },
                {"x": 8, "y": 0, "w": 4, "h": 3},
            ),
            (
                "Smoke Pie",
                "pie",
                {
                    "aggregate": "count",
                    "event_name": csv_event,
                    "group_by": "property:plan",
                    "time_bucket": None,
                },
                {"x": 0, "y": 3, "w": 4, "h": 3},
            ),
            (
                "Smoke Table",
                "table",
                {"aggregate": "count", "group_by": "event_name", "time_bucket": None},
                {"x": 4, "y": 3, "w": 8, "h": 3},
            ),
        ]

        widget_ids: list[str] = []
        for title, kind, query, layout in widget_specs:
            response = await request(
                client,
                "POST",
                f"/dashboards/{dashboard_id}/widgets",
                expected=201,
                token=owner_token,
                json={
                    "title": title,
                    "kind": kind,
                    "query": {"filters": [], **query},
                    "layout": layout,
                },
            )
            widget_ids.append(response.json()["id"])

        await wait_for_widget_rows(
            client,
            token=owner_token,
            widget_id=widget_ids[0],
            min_value=1,
        )
        for widget_id in widget_ids:
            data = await request(
                client,
                "GET",
                f"/dashboards/widgets/{widget_id}/data",
                expected=200,
                token=owner_token,
            )
            assert isinstance(data.json()["rows"], list)

        detail = await request(
            client,
            "GET",
            f"/dashboards/{dashboard_id}",
            expected=200,
            token=owner_token,
        )
        assert len(detail.json()["widgets"]) == 5

        share = await request(
            client,
            "POST",
            f"/dashboards/{dashboard_id}/share",
            expected=200,
            token=owner_token,
        )
        share_token = share.json()["share_token"]
        await request(
            client,
            "GET",
            f"/public/dashboards/{share_token}",
            expected=200,
        )
        await request(
            client,
            "GET",
            f"/public/dashboards/{share_token}/widgets/{widget_ids[0]}/data",
            expected=200,
        )
        await request(
            client,
            "PATCH",
            f"/public/dashboards/{share_token}",
            expected={404, 405},
            json={"name": "public write should fail"},
        )

        other_signup = await request(
            client,
            "POST",
            "/auth/signup",
            expected=201,
            json={
                "organization_name": f"Smoke Other Org {nonce}",
                "full_name": "Other Owner",
                "email": f"other-owner-{nonce}@example.com",
                "password": OWNER_PASSWORD,
            },
        )
        other_token = other_signup.json()["access_token"]
        await request(
            client,
            "GET",
            f"/dashboards/{dashboard_id}",
            expected=404,
            token=other_token,
        )

        await request(client, "POST", "/auth/logout", expected=200, token=owner_token)
        await request(client, "POST", "/auth/refresh", expected=401)

    print("Live smoke passed")
    print(f"Dashboard created: Smoke Dashboard {nonce}")
    print(
        "Covered: auth, refresh/logout, invites, RBAC, API keys, ingestion, CSV, "
        "widgets, sharing"
    )


if __name__ == "__main__":
    asyncio.run(run())
