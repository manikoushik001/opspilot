import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.knowledge_document import KnowledgeDocument, DocumentStatus
from app.models.knowledge_chunk import KnowledgeChunk
from app.ai.service import AIService


@pytest.mark.asyncio
async def test_cross_tenant_customer_access_blocked(
    client: AsyncClient,
    tenant_a_data: dict,
    tenant_b_data: dict
):
    headers_a = tenant_a_data["headers_owner"]
    customer_b_id = tenant_b_data["customer"].id

    # 1. Tenant A tries to read Tenant B customer -> 404
    resp = await client.get(f"/api/v1/customers/{customer_b_id}", headers=headers_a)
    assert resp.status_code == 404

    # 2. Tenant A tries to update Tenant B customer -> 404
    resp = await client.patch(
        f"/api/v1/customers/{customer_b_id}",
        json={"name": "Hacked Name"},
        headers=headers_a
    )
    assert resp.status_code == 404

    # 3. Tenant A tries to delete Tenant B customer -> 404
    resp = await client.delete(f"/api/v1/customers/{customer_b_id}", headers=headers_a)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_tenant_spoofing_header_rejected(
    client: AsyncClient,
    tenant_a_data: dict,
    tenant_b_data: dict
):
    # Owner A tries to pass X-Business-ID: biz-b-222 (Tenant B's ID)
    spoofed_headers = {
        "Authorization": f"Bearer {tenant_a_data['owner_token']}",
        "X-Business-ID": tenant_b_data["business"].id
    }

    # Should be rejected with 403 Forbidden because User A is not a member of Business B
    resp = await client.get("/api/v1/customers", headers=spoofed_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_rag_vector_search_tenant_isolation(
    test_db: AsyncSession,
    tenant_a_data: dict,
    tenant_b_data: dict
):
    biz_a_id = tenant_a_data["business"].id
    biz_b_id = tenant_b_data["business"].id

    # Add secret knowledge document & chunk to Business B
    doc_b = KnowledgeDocument(
        id="doc-b-secret",
        business_id=biz_b_id,
        filename="confidential_b.txt",
        mime_type="text/plain",
        storage_path="/tmp/confidential_b.txt",
        status=DocumentStatus.READY,
        chunk_count=1
    )
    test_db.add(doc_b)
    await test_db.flush()

    ai_svc = AIService(test_db)
    chunk_vec = await ai_svc.create_embedding("Special secret discount code for Business B is SECRET_B_999")

    chunk_b = KnowledgeChunk(
        business_id=biz_b_id,
        document_id=doc_b.id,
        chunk_index=0,
        content="Special secret discount code for Business B is SECRET_B_999"
    )
    chunk_b.embedding = chunk_vec
    test_db.add(chunk_b)
    await test_db.flush()

    # Query RAG for Business A with the same query
    retrieved_a = await ai_svc.retrieve_context(
        business_id=biz_a_id,
        query="What is the secret discount code?",
        top_k=4,
        similarity_threshold=0.1
    )

    # Must be empty for Business A (zero cross-tenant vector leakage)
    assert len(retrieved_a) == 0

    # Query RAG for Business B should retrieve it
    retrieved_b = await ai_svc.retrieve_context(
        business_id=biz_b_id,
        query="What is the secret discount code?",
        top_k=4,
        similarity_threshold=0.1
    )
    assert len(retrieved_b) == 1
    assert "SECRET_B_999" in retrieved_b[0]["content"]
