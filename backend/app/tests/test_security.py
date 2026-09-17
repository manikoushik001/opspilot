import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_unauthenticated(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_unauthorized_endpoints_reject_invalid_token(client: AsyncClient):
    resp = await client.get(
        "/api/v1/customers",
        headers={"Authorization": "Bearer invalid-token-string-123"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_staff_role_cannot_access_owner_only_resources(
    client: AsyncClient,
    tenant_a_data: dict
):
    headers_staff = tenant_a_data["headers_staff"]

    # 1. Staff cannot view audit logs (Owner-only)
    resp = await client.get("/api/v1/audit-logs", headers=headers_staff)
    assert resp.status_code == 403

    # 2. Staff cannot patch business settings (Owner-only)
    resp = await client.patch(
        "/api/v1/business",
        json={"name": "Malicious Business Rename"},
        headers=headers_staff
    )
    assert resp.status_code == 403
