import enum
from sqlalchemy import Column, String, Text, ForeignKey, Enum, DateTime, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class FollowupStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Followup(BaseModel):
    __tablename__ = "followups"
    __table_args__ = (
        Index("ix_followups_business_status", "business_id", "status"),
        Index("ix_followups_due_at", "due_at"),
    )

    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), index=True, nullable=False)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="SET NULL"), index=True, nullable=True)
    assigned_to = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(FollowupStatus), default=FollowupStatus.PENDING, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    business = relationship("Business", back_populates="followups")
    customer = relationship("Customer", back_populates="followups")
    conversation = relationship("Conversation", back_populates="followups")
    assigned_user = relationship("User", foreign_keys=[assigned_to])
