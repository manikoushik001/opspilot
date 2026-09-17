from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Business(BaseModel):
    __tablename__ = "businesses"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    industry = Column(String(100), nullable=True, default="Education")
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    timezone = Column(String(50), default="UTC", nullable=False)

    members = relationship("BusinessMember", back_populates="business", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="business", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="business", cascade="all, delete-orphan")
    knowledge_documents = relationship("KnowledgeDocument", back_populates="business", cascade="all, delete-orphan")
    followups = relationship("Followup", back_populates="business", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="business", cascade="all, delete-orphan")
