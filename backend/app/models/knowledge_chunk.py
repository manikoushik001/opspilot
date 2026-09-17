import json
from sqlalchemy import Column, String, Text, ForeignKey, Integer, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class KnowledgeChunk(BaseModel):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        Index("ix_knowledge_chunks_business", "business_id"),
        Index("ix_knowledge_chunks_doc", "document_id"),
    )

    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    document_id = Column(String(36), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), index=True, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding_json = Column(Text, nullable=True)  # JSON-encoded vector
    meta_json = Column(Text, nullable=True)       # JSON-encoded metadata (page, filename, etc.)

    document = relationship("KnowledgeDocument", back_populates="chunks")

    @property
    def embedding(self):
        if self.embedding_json:
            return json.loads(self.embedding_json)
        return []

    @embedding.setter
    def embedding(self, value):
        if value is not None:
            self.embedding_json = json.dumps(value)
        else:
            self.embedding_json = None

    @property
    def metadata_dict(self):
        if self.meta_json:
            return json.loads(self.meta_json)
        return {}

    @metadata_dict.setter
    def metadata_dict(self, value):
        if value is not None:
            self.meta_json = json.dumps(value)
        else:
            self.meta_json = "{}"
