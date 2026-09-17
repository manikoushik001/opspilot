import os
import aiofiles
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.core.logging import get_logger
from app.models.knowledge_document import KnowledgeDocument, DocumentStatus
from app.models.knowledge_chunk import KnowledgeChunk
from app.ai.chunking import chunk_text
from app.ai.service import AIService
from app.services.audit_service import AuditService

logger = get_logger("knowledge.service")


class KnowledgeService:
    @staticmethod
    async def list_documents(db: AsyncSession, business_id: str) -> List[KnowledgeDocument]:
        stmt = (
            select(KnowledgeDocument)
            .where(KnowledgeDocument.business_id == business_id)
            .order_by(KnowledgeDocument.created_at.desc())
        )
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def get_document(db: AsyncSession, business_id: str, document_id: str) -> KnowledgeDocument:
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.business_id == business_id
        )
        res = await db.execute(stmt)
        doc = res.scalar_one_or_none()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge document not found."
            )
        return doc

    @staticmethod
    async def upload_and_process_document(
        db: AsyncSession,
        business_id: str,
        user_id: str,
        file: UploadFile
    ) -> KnowledgeDocument:
        os.makedirs(settings.LOCAL_STORAGE_DIR, exist_ok=True)
        filename = file.filename or "uploaded_doc.txt"
        file_ext = os.path.splitext(filename)[1].lower()
        mime_type = file.content_type or "text/plain"

        # Validate file type
        allowed_exts = [".txt", ".md", ".pdf", ".json", ".csv"]
        if file_ext not in allowed_exts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{file_ext}'. Allowed formats: {', '.join(allowed_exts)}"
            )

        storage_filename = f"{business_id}_{filename}"
        storage_path = os.path.join(settings.LOCAL_STORAGE_DIR, storage_filename)

        # Save to storage
        content_bytes = await file.read()
        async with aiofiles.open(storage_path, "wb") as f:
            await f.write(content_bytes)

        # Create Document Record
        doc = KnowledgeDocument(
            business_id=business_id,
            filename=filename,
            mime_type=mime_type,
            storage_path=storage_path,
            status=DocumentStatus.PROCESSING
        )
        db.add(doc)
        await db.flush()

        try:
            # Process synchronously or background
            await KnowledgeService.process_document_content(db, doc, content_bytes, file_ext)
            doc.status = DocumentStatus.READY
            await db.flush()

            await AuditService.log_action(
                db=db,
                business_id=business_id,
                action="KNOWLEDGE_UPLOADED",
                resource_type="knowledge_document",
                resource_id=doc.id,
                user_id=user_id,
                metadata={"filename": filename, "chunks": doc.chunk_count}
            )
        except Exception as e:
            logger.error(f"Failed processing document {filename}: {str(e)}", exc_info=True)
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            await db.flush()

        return doc

    @staticmethod
    async def process_document_content(
        db: AsyncSession,
        doc: KnowledgeDocument,
        content_bytes: bytes,
        file_ext: str
    ):
        extracted_text = ""
        page_chunks = []

        if file_ext == ".pdf":
            try:
                import pypdf
                import io
                reader = pypdf.PdfReader(io.BytesIO(content_bytes))
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        chunks = chunk_text(page_text, chunk_size=500, chunk_overlap=50, metadata={"page": page_num + 1, "filename": doc.filename})
                        page_chunks.extend(chunks)
            except Exception as pdf_err:
                logger.warning(f"PDF extraction fallback: {pdf_err}")
                extracted_text = content_bytes.decode("utf-8", errors="ignore")
                page_chunks = chunk_text(extracted_text, chunk_size=500, chunk_overlap=50, metadata={"filename": doc.filename})
        else:
            extracted_text = content_bytes.decode("utf-8", errors="ignore")
            page_chunks = chunk_text(extracted_text, chunk_size=500, chunk_overlap=50, metadata={"filename": doc.filename})

        ai_svc = AIService(db)
        chunk_count = 0

        for item in page_chunks:
            chunk_vec = await ai_svc.create_embedding(item["content"])
            chunk_record = KnowledgeChunk(
                business_id=doc.business_id,
                document_id=doc.id,
                chunk_index=item["chunk_index"],
                content=item["content"]
            )
            chunk_record.embedding = chunk_vec
            chunk_record.metadata_dict = item.get("metadata", {})
            db.add(chunk_record)
            chunk_count += 1

        doc.chunk_count = chunk_count

    @staticmethod
    async def delete_document(
        db: AsyncSession,
        business_id: str,
        document_id: str,
        user_id: str
    ) -> bool:
        doc = await KnowledgeService.get_document(db, business_id, document_id)
        if os.path.exists(doc.storage_path):
            try:
                os.remove(doc.storage_path)
            except OSError:
                pass

        await db.delete(doc)
        await db.flush()

        await AuditService.log_action(
            db=db,
            business_id=business_id,
            action="KNOWLEDGE_DELETED",
            resource_type="knowledge_document",
            resource_id=document_id,
            user_id=user_id,
            metadata={"filename": doc.filename}
        )
        return True
