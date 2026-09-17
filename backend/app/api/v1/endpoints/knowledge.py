from typing import Tuple, List
from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.schemas.knowledge import (
    KnowledgeDocumentOut, KnowledgeChunkOut,
    KnowledgeSearchQuery, KnowledgeSearchResult
)
from app.models.knowledge_document import KnowledgeDocument
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.user import User
from app.models.membership import BusinessMember
from app.services.knowledge_service import KnowledgeService
from app.ai.service import AIService
from app.api.deps import get_current_business_membership, require_owner_role

router = APIRouter()


@router.get("/documents", response_model=List[KnowledgeDocumentOut])
async def list_documents(
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    return await KnowledgeService.list_documents(db, membership.business_id)


@router.post("/documents", response_model=KnowledgeDocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    auth_data: Tuple[User, BusinessMember] = Depends(require_owner_role),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    return await KnowledgeService.upload_and_process_document(
        db=db,
        business_id=membership.business_id,
        user_id=user.id,
        file=file
    )


@router.get("/documents/{document_id}", response_model=KnowledgeDocumentOut)
async def get_document(
    document_id: str,
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    return await KnowledgeService.get_document(db, membership.business_id, document_id)


@router.get("/documents/{document_id}/chunks", response_model=List[KnowledgeChunkOut])
async def get_document_chunks(
    document_id: str,
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    # Verify doc belongs to tenant
    await KnowledgeService.get_document(db, membership.business_id, document_id)

    stmt = select(KnowledgeChunk).where(
        KnowledgeChunk.document_id == document_id,
        KnowledgeChunk.business_id == membership.business_id
    ).order_by(KnowledgeChunk.chunk_index.asc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    auth_data: Tuple[User, BusinessMember] = Depends(require_owner_role),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    await KnowledgeService.delete_document(db, membership.business_id, document_id, user.id)
    return None


@router.post("/search", response_model=List[KnowledgeSearchResult])
async def search_knowledge(
    search_query: KnowledgeSearchQuery,
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    ai_svc = AIService(db)
    results = await ai_svc.retrieve_context(
        business_id=membership.business_id,
        query=search_query.query,
        top_k=search_query.top_k or settings.RAG_TOP_K,
        similarity_threshold=search_query.similarity_threshold or settings.RAG_SIMILARITY_THRESHOLD
    )
    return [
        KnowledgeSearchResult(
            chunk_id=r["chunk_id"],
            document_id=r["document_id"],
            filename=r["filename"],
            content=r["content"],
            similarity_score=r["similarity_score"],
            chunk_index=r["chunk_index"],
            metadata=r["metadata"]
        )
        for r in results
    ]
