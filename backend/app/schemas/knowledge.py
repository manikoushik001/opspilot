from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.knowledge_document import DocumentStatus


class KnowledgeDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    filename: str
    mime_type: str
    status: DocumentStatus
    chunk_count: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class KnowledgeChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    chunk_index: int
    content: str
    metadata_dict: Dict[str, Any] = {}
    created_at: datetime


class KnowledgeSearchQuery(BaseModel):
    query: str
    top_k: Optional[int] = 4
    similarity_threshold: Optional[float] = 0.60


class KnowledgeSearchResult(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    content: str
    similarity_score: float
    chunk_index: int
    metadata: Dict[str, Any] = {}
