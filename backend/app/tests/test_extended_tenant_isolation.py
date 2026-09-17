import pytest
from httpx import AsyncClient
from fastapi import status
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_cross_tenant_conversation_isolation(
    client: AsyncClient,
    tenant_a_data: dict,
    tenant_b_data: dict
):
    headers_a = tenant_a_data["headers_owner"]
    headers_b = tenant_b_data["headers_owner"]
    
    # 1. Tenant A creates conversation
    create_payload = {
        "customer_id": tenant_a_data["customer"].id,
        "channel": "WEB_CHAT",
        "subject": "Inquiry about Python"
    }
    res_a = await client.post("/api/v1/conversations", headers=headers_a, json=create_payload)
    assert res_a.status_code == status.HTTP_201_CREATED
    conv_a_id = res_a.json()["id"]
    
    # 2. Tenant B attempts to read Tenant A's conversation -> must be 404
    res_b_read = await client.get(f"/api/v1/conversations/{conv_a_id}", headers=headers_b)
    assert res_b_read.status_code == status.HTTP_404_NOT_FOUND
    
    # 3. Tenant B attempts to send message into Tenant A's conversation -> must be 404
    msg_payload = {
        "conversation_id": conv_a_id,
        "sender_type": "CUSTOMER",
        "content": "Malicious cross-tenant injection"
    }
    res_b_msg = await client.post(f"/api/v1/conversations/{conv_a_id}/messages", headers=headers_b, json=msg_payload)
    assert res_b_msg.status_code == status.HTTP_404_NOT_FOUND
    
    # 4. Tenant B attempts to close Tenant A's conversation -> must be 404
    res_b_close = await client.patch(f"/api/v1/conversations/{conv_a_id}/close", headers=headers_b)
    assert res_b_close.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_cross_tenant_followup_isolation(
    client: AsyncClient,
    tenant_a_data: dict,
    tenant_b_data: dict
):
    headers_a = tenant_a_data["headers_owner"]
    headers_b = tenant_b_data["headers_owner"]
    
    # 1. Tenant A creates a follow-up
    create_followup = {
        "customer_id": tenant_a_data["customer"].id,
        "title": "Call student regarding fee deposit",
        "due_at": datetime.now(timezone.utc).isoformat()
    }
    res_a = await client.post("/api/v1/followups", headers=headers_a, json=create_followup)
    assert res_a.status_code == status.HTTP_201_CREATED
    followup_a_id = res_a.json()["id"]
    
    # 2. Tenant B attempts to view Tenant A's follow-up -> must be 404
    res_b_get = await client.get(f"/api/v1/followups/{followup_a_id}", headers=headers_b)
    assert res_b_get.status_code == status.HTTP_404_NOT_FOUND
    
    # 3. Tenant B attempts to mark Tenant A's follow-up complete -> must be 404
    res_b_done = await client.patch(f"/api/v1/followups/{followup_a_id}/complete", headers=headers_b)
    assert res_b_done.status_code == status.HTTP_404_NOT_FOUND
    
    # 4. Tenant B listing followups only sees their own (0 items)
    res_b_list = await client.get("/api/v1/followups", headers=headers_b)
    assert res_b_list.status_code == status.HTTP_200_OK
    assert len(res_b_list.json()["items"]) == 0


@pytest.mark.asyncio
async def test_cross_tenant_audit_logs_isolation(
    client: AsyncClient,
    tenant_a_data: dict,
    tenant_b_data: dict
):
    headers_a = tenant_a_data["headers_owner"]
    headers_b = tenant_b_data["headers_owner"]
    
    # Query audit logs for Tenant B -> must not show any activities from Tenant A
    res_b = await client.get("/api/v1/audit-logs", headers=headers_b)
    assert res_b.status_code == status.HTTP_200_OK
    logs_b = res_b.json()
    for log in logs_b["items"]:
        assert log["business_id"] == tenant_b_data["business"].id
