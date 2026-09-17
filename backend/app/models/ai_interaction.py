from sqlalchemy import Column, String, ForeignKey, Float, Integer, Boolean, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class AIInteraction(BaseModel):
    __tablename__ = "ai_interactions"
    __table_args__ = (
        Index("ix_ai_interactions_business", "business_id"),
        Index("ix_ai_interactions_created", "created_at"),
    )

    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="SET NULL"), index=True, nullable=True)
    message_id = Column(String(36), nullable=True)
    model = Column(String(100), nullable=False)
    operation = Column(String(100), nullable=False)  # "classify", "answer", "suggest_action"
    confidence = Column(Float, nullable=True)
    retrieval_count = Column(Integer, default=0, nullable=False)
    latency_ms = Column(Integer, default=0, nullable=False)
    success = Column(Boolean, default=True, nullable=False)

    conversation = relationship("Conversation", back_populates="ai_interactions")
