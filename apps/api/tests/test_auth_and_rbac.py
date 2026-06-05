from httpx import AsyncClient

from tests.helpers import signup


async def test_auth_positive_signup_refresh_logout(client: AsyncClient) -> None:
    token, profile = await signup(client)

    assert profile["role"] == "Owner"
    refresh = await client.post("/api/v1/auth/refresh")
    assert refresh.status_code == 200, refresh.text
    assert refresh.json()["access_token"]

    logout = await client.post("/api/v1/auth/logout")
    assert logout.status_code == 200


async def test_auth_negative_wrong_password_returns_structured_error(client: AsyncClient) -> None:
    await signup(client)
    response = await client.post(
        "/api/v1/auth/signin",
        json={"email": "owner@example.com", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_failed"
    assert response.json()["error"]["request_id"]


async def test_false_positive_viewer_cannot_create_api_key(client: AsyncClient) -> None:
    owner_token, _profile = await signup(client)
    invite = await client.post(
        "/api/v1/organizations/invites",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"email": "viewer@example.com", "role": "Viewer"},
    )
    assert invite.status_code == 201, invite.text
    outbox = await client.get(
        "/api/v1/organizations/dev-outbox",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    token = outbox.json()[0]["payload"]["token"]
    accepted = await client.post(
        "/api/v1/organizations/invites/accept",
        json={"token": token, "full_name": "Viewer User", "password": "Password123!"},
    )
    assert accepted.status_code == 200

    signin = await client.post(
        "/api/v1/auth/signin",
        json={"email": "viewer@example.com", "password": "Password123!"},
    )
    viewer_token = signin.json()["access_token"]
    response = await client.post(
        "/api/v1/api-keys",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"name": "Should fail"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"
