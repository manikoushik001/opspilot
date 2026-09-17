import enum
from sqlalchemy import Column, String, Text, ForeignKey, Enum, Integer, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class DocumentStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class KnowledgeDocument(BaseModel):
    __tablename__ = "knowledge_documents"
    __table_args__ = (
        Index("ix_knowledge_docs_business_status", "business_id", "status"),
    )

    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    storage_path = Column(String(500), nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False)
    error_message = Column(Text, nullable=True)
    chunk_count = Column(Integer, default=0, nullable=False)

    business = relationship("Business", back_populates="knowledge_documents")
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan", order_by="KnowledgeChunk.chunk_index")
