import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_conversation_lifecycle_and_messages(client: AsyncClient, tenant_a_data: dict):
    headers = tenant_a_data["headers_owner"]
    cust_id = tenant_a_data["customer"].id

    # 1. Create conversation
    conv_resp = await client.post(
        "/api/v1/conversations",
        json={
            "customer_id": cust_id,
            "priority": "MEDIUM",
            "initial_message": "Hello, I have a question about class schedules."
        },
        headers=headers
    )
    assert conv_resp.status_code == 201
    conv = conv_resp.json()
    conv_id = conv["id"]
    assert conv["status"] == "OPEN"

    # Check detail contains the initial message
    detail_resp = await client.get(f"/api/v1/conversations/{conv_id}", headers=headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["messages"]) == 1
    assert detail["messages"][0]["sender_type"] == "CUSTOMER"

    # 2. Staff replies
    staff_resp = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Hi Alice! Classes are held on Saturdays and Sundays.", "sender_type": "STAFF"},
        headers=headers
    )
    assert staff_resp.status_code == 201
    assert staff_resp.json()["sender_type"] == "STAFF"

    # 3. Simulate customer message through AI pipeline
    sim_resp = await client.post(
        f"/api/v1/conversations/{conv_id}/simulate-customer",
        json={"content": "What is the fee for the weekend Java course?"},
        headers=headers
    )
    assert sim_resp.status_code == 200
    sim_data = sim_resp.json()
    assert sim_data["customer_message"]["sender_type"] == "CUSTOMER"
    assert sim_data["ai_response"]["sender_type"] == "AI"
    assert sim_data["decision_metadata"]["intent"] == "PRICE_QUERY"
    assert sim_data["decision_metadata"]["confidence"] >= 0.50

    # 4. Resolve conversation
    update_resp = await client.patch(
        f"/api/v1/conversations/{conv_id}",
        json={"status": "RESOLVED"},
        headers=headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "RESOLVED"
    assert update_resp.json()["resolved_at"] is not None
