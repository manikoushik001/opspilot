import os
import asyncio
from app.workers.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.knowledge_document import KnowledgeDocument, DocumentStatus
from app.services.knowledge_service import KnowledgeService
from app.core.logging import get_logger

logger = get_logger("worker.tasks")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_document_task(self, document_id: str, business_id: str):
    """
    Background worker task to extract, chunk, and embed uploaded documents.
    """
    async def _async_process():
        async with AsyncSessionLocal() as db:
            try:
                doc = await KnowledgeService.get_document(db, business_id, document_id)
                if not os.path.exists(doc.storage_path):
                    doc.status = DocumentStatus.FAILED
                    doc.error_message = f"File missing at {doc.storage_path}"
                    await db.commit()
                    return {"status": "failed", "error": doc.error_message}

                with open(doc.storage_path, "rb") as f:
                    content_bytes = f.read()

                file_ext = os.path.splitext(doc.filename)[1].lower()
                await KnowledgeService.process_document_content(db, doc, content_bytes, file_ext)
                doc.status = DocumentStatus.READY
                await db.commit()
                return {"status": "success", "chunks": doc.chunk_count}
            except Exception as exc:
                logger.error(f"Task error processing document {document_id}: {exc}", exc_info=True)
                await db.rollback()
                raise exc

    loop = asyncio.get_event_loop()
    if loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, _async_process()).result()
    else:
        return asyncio.run(_async_process())
