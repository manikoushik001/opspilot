import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_customer_crud_operations(client: AsyncClient, tenant_a_data: dict):
    headers = tenant_a_data["headers_owner"]

    # 1. List initial customers
    list_resp = await client.get("/api/v1/customers", headers=headers)
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] >= 1
    assert data["items"][0]["name"] == "Alice TenantA"

    # 2. Create customer
    create_resp = await client.post(
        "/api/v1/customers",
        json={
            "name": "Charlie Student",
            "email": "charlie@example.com",
            "phone": "555-9876",
            "status": "NEW",
            "notes": "Interested in full-stack Java track"
        },
        headers=headers
    )
    assert create_resp.status_code == 201
    created_cust = create_resp.json()
    assert created_cust["name"] == "Charlie Student"
    cust_id = created_cust["id"]

    # 3. Update customer
    patch_resp = await client.patch(
        f"/api/v1/customers/{cust_id}",
        json={"status": "ACTIVE", "notes": "Enrolled in weekend batch"},
        headers=headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "ACTIVE"
    assert patch_resp.json()["notes"] == "Enrolled in weekend batch"

    # 4. Search customer
    search_resp = await client.get("/api/v1/customers?search=Charlie", headers=headers)
    assert search_resp.status_code == 200
    assert search_resp.json()["total"] == 1
    assert search_resp.json()["items"][0]["name"] == "Charlie Student"

    # 5. Delete customer
    del_resp = await client.delete(f"/api/v1/customers/{cust_id}", headers=headers)
    assert del_resp.status_code == 204

    # Verify deleted
    get_resp = await client.get(f"/api/v1/customers/{cust_id}", headers=headers)
    assert get_resp.status_code == 404
