import enum
from sqlalchemy import Column, String, Text, ForeignKey, Enum, Float, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class SenderType(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    STAFF = "STAFF"
    AI = "AI"


class MessageIntent(str, enum.Enum):
    COURSE_INFORMATION = "COURSE_INFORMATION"
    PRICE_QUERY = "PRICE_QUERY"
    APPOINTMENT_REQUEST = "APPOINTMENT_REQUEST"
    COMPLAINT = "COMPLAINT"
    REFUND_REQUEST = "REFUND_REQUEST"
    FOLLOW_UP = "FOLLOW_UP"
    GENERAL_INFORMATION = "GENERAL_INFORMATION"
    OTHER = "OTHER"


class Message(BaseModel):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
    )

    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    sender_type = Column(Enum(SenderType), nullable=False)
    sender_id = Column(String(36), nullable=True)  # User ID if staff, Customer ID if customer, "ai" if AI
    content = Column(Text, nullable=False)
    intent = Column(Enum(MessageIntent), nullable=True)
    ai_confidence = Column(Float, nullable=True)

    conversation = relationship("Conversation", back_populates="messages")
