import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_analytics_overview_endpoint(client: AsyncClient, tenant_a_data: dict):
    headers = tenant_a_data["headers_owner"]

    resp = await client.get("/api/v1/analytics/overview", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert "total_customers" in data
    assert "total_conversations" in data
    assert "resolution_breakdown" in data
    assert "daily_volume" in data
    assert "avg_ai_confidence" in data
    assert isinstance(data["intent_distribution"], list)
