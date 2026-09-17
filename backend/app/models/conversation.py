import enum
from sqlalchemy import Column, String, ForeignKey, Enum, DateTime, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ConversationStatus(str, enum.Enum):
    OPEN = "OPEN"
    WAITING = "WAITING"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class ConversationPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class Conversation(BaseModel):
    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversations_business_status", "business_id", "status"),
        Index("ix_conversations_business_created", "business_id", "created_at"),
    )

    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), index=True, nullable=False)
    status = Column(Enum(ConversationStatus), default=ConversationStatus.OPEN, nullable=False)
    priority = Column(Enum(ConversationPriority), default=ConversationPriority.MEDIUM, nullable=False)
    assigned_to = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    business = relationship("Business", back_populates="conversations")
    customer = relationship("Customer", back_populates="conversations")
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    followups = relationship("Followup", back_populates="conversation", cascade="all, delete-orphan")
    ai_interactions = relationship("AIInteraction", back_populates="conversation", cascade="all, delete-orphan")
    ai_actions = relationship("AIAction", back_populates="conversation", cascade="all, delete-orphan")
