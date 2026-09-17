from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_followup_crud_and_status(client: AsyncClient, tenant_a_data: dict):
    headers = tenant_a_data["headers_owner"]
    cust_id = tenant_a_data["customer"].id

    due_future = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

    # 1. Create Followup
    create_resp = await client.post(
        "/api/v1/followups",
        json={
            "customer_id": cust_id,
            "title": "Send syllabus PDF",
            "description": "Customer requested detailed curriculum breakdown",
            "due_at": due_future
        },
        headers=headers
    )
    assert create_resp.status_code == 201
    followup = create_resp.json()
    followup_id = followup["id"]
    assert followup["status"] == "PENDING"
    assert followup["is_overdue"] is False

    # 2. Mark completed
    update_resp = await client.patch(
        f"/api/v1/followups/{followup_id}",
        json={"status": "COMPLETED"},
        headers=headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "COMPLETED"
    assert update_resp.json()["completed_at"] is not None
