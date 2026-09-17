from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.followup import FollowupStatus
from app.schemas.customer import CustomerOut


class FollowupBase(BaseModel):
    customer_id: str
    conversation_id: Optional[str] = None
    assigned_to: Optional[str] = None
    title: str
    description: Optional[str] = None
    due_at: datetime


class FollowupCreate(FollowupBase):
    pass


class FollowupUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_at: Optional[datetime] = None
    status: Optional[FollowupStatus] = None
    assigned_to: Optional[str] = None


class FollowupOut(FollowupBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    status: FollowupStatus
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_overdue: bool = False
    customer: Optional[CustomerOut] = None


class FollowupListResponse(BaseModel):
    items: List[FollowupOut]
    total: int
    pending_count: int
    overdue_count: int
    completed_count: int
