import enum
from sqlalchemy import Column, String, Text, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class CustomerStatus(str, enum.Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    FOLLOW_UP = "FOLLOW_UP"
    RESOLVED = "RESOLVED"
    INACTIVE = "INACTIVE"


class Customer(BaseModel):
    __tablename__ = "customers"
    __table_args__ = (
        Index("ix_customers_business_status", "business_id", "status"),
        Index("ix_customers_business_email", "business_id", "email"),
    )

    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    status = Column(Enum(CustomerStatus), default=CustomerStatus.NEW, nullable=False)
    notes = Column(Text, nullable=True)

    business = relationship("Business", back_populates="customers")
    conversations = relationship("Conversation", back_populates="customer", cascade="all, delete-orphan")
    followups = relationship("Followup", back_populates="customer", cascade="all, delete-orphan")
