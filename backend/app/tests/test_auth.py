import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_flow(client: AsyncClient):
    # 1. Register
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "strongpassword123",
            "full_name": "Test User",
            "business_name": "Test Learning Center"
        }
    )
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()
    assert user_data["email"] == "testuser@example.com"
    assert user_data["full_name"] == "Test User"
    assert len(user_data["memberships"]) == 1
    assert user_data["memberships"][0]["role"] == "OWNER"

    # 2. Duplicate registration fails
    dup_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "anotherpassword",
            "full_name": "Duplicate User"
        }
    )
    assert dup_resp.status_code == 400

    # 3. Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "strongpassword123"
        }
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data

    # 4. Get Current User (/me)
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_data['access_token']}"}
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "testuser@example.com"


@pytest.mark.asyncio
async def test_invalid_login(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
    )
    assert resp.status_code == 401
