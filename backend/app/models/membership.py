import enum
from sqlalchemy import Column, String, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class MemberRole(str, enum.Enum):
    OWNER = "OWNER"
    STAFF = "STAFF"


class BusinessMember(BaseModel):
    __tablename__ = "business_members"
    __table_args__ = (
        UniqueConstraint("business_id", "user_id", name="uq_business_user"),
    )

    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    role = Column(Enum(MemberRole), default=MemberRole.STAFF, nullable=False)

    user = relationship("User", back_populates="memberships")
    business = relationship("Business", back_populates="members")
