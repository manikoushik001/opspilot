import io
import pytest
from httpx import AsyncClient
from fastapi import status

@pytest.mark.asyncio
async def test_knowledge_document_lifecycle(
    client: AsyncClient,
    tenant_a_data: dict
):
    headers = tenant_a_data["headers_owner"]
    staff_headers = tenant_a_data["headers_staff"]
    
    # 1. Upload Markdown doc as OWNER
    file_content = b"# Machine Learning Course\n\nTuition is $1200.\nClasses are held online every Saturday.\nRefunds must be requested within 7 days."
    files = {"file": ("courses.md", io.BytesIO(file_content), "text/markdown")}
    
    upload_resp = await client.post("/api/v1/knowledge/documents", headers=headers, files=files)
    assert upload_resp.status_code == status.HTTP_201_CREATED
    doc_data = upload_resp.json()
    doc_id = doc_data["id"]
    assert doc_data["filename"] == "courses.md"
    assert doc_data["status"] == "READY"
    
    # 2. List documents
    list_resp = await client.get("/api/v1/knowledge/documents", headers=headers)
    assert list_resp.status_code == status.HTTP_200_OK
    docs = list_resp.json()
    assert any(d["id"] == doc_id for d in docs)
    
    # 3. Get document chunks
    chunks_resp = await client.get(f"/api/v1/knowledge/documents/{doc_id}/chunks", headers=headers)
    assert chunks_resp.status_code == status.HTTP_200_OK
    chunks = chunks_resp.json()
    assert len(chunks) > 0
    assert any("Tuition" in c["content"] or "Machine Learning" in c["content"] for c in chunks)
    
    # 4. Search knowledge base
    search_payload = {"query": "How much is the Machine Learning tuition fee?", "top_k": 3}
    search_resp = await client.post("/api/v1/knowledge/search", headers=headers, json=search_payload)
    assert search_resp.status_code == status.HTTP_200_OK
    search_results = search_resp.json()
    assert len(search_results) > 0
    
    # 5. Staff role cannot upload or delete documents
    staff_upload = await client.post(
        "/api/v1/knowledge/documents",
        headers=staff_headers,
        files={"file": ("staff.md", io.BytesIO(b"content"), "text/markdown")}
    )
    assert staff_upload.status_code == status.HTTP_403_FORBIDDEN
    
    staff_delete = await client.delete(f"/api/v1/knowledge/documents/{doc_id}", headers=staff_headers)
    assert staff_delete.status_code == status.HTTP_403_FORBIDDEN
    
    # 6. Delete document as owner
    del_resp = await client.delete(f"/api/v1/knowledge/documents/{doc_id}", headers=headers)
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT
    
    # 7. Document should no longer be found
    get_resp = await client.get(f"/api/v1/knowledge/documents/{doc_id}", headers=headers)
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_unsupported_file_upload_rejected(
    client: AsyncClient,
    tenant_a_data: dict
):
    headers = tenant_a_data["headers_owner"]
    files = {"file": ("malicious.exe", io.BytesIO(b"\x4D\x5A\x90\x00"), "application/x-msdownload")}
    
    upload_resp = await client.post("/api/v1/knowledge/documents", headers=headers, files=files)
    assert upload_resp.status_code == status.HTTP_400_BAD_REQUEST
