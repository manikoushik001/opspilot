import json
from sqlalchemy import Column, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_business_created", "business_id", "created_at"),
        Index("ix_audit_logs_action", "action"),
    )

    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=True)
    metadata_json = Column(Text, nullable=True)

    business = relationship("Business", back_populates="audit_logs")
    user = relationship("User")

    @property
    def metadata_dict(self):
        if self.metadata_json:
            return json.loads(self.metadata_json)
        return {}

    @metadata_dict.setter
    def metadata_dict(self, value):
        if value is not None:
            self.metadata_json = json.dumps(value)
        else:
            self.metadata_json = "{}"
