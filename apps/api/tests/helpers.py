from httpx import AsyncClient


async def signup(
    client: AsyncClient,
    *,
    email: str = "owner@example.com",
    org: str = "Acme Analytics",
    password: str = "Password123!",
) -> tuple[str, dict]:
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "full_name": "Owner User",
            "password": password,
            "organization_name": org,
        },
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200, me.text
    return token, me.json()


async def create_api_key(client: AsyncClient, token: str) -> str:
    response = await client.post(
        "/api/v1/api-keys",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Ingestion"},
    )
    assert response.status_code == 201, response.text
    return response.json()["key"]

