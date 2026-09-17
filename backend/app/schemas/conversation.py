from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.conversation import ConversationStatus, ConversationPriority
from app.schemas.customer import CustomerOut
from app.schemas.message import MessageOut


class ConversationBase(BaseModel):
    customer_id: str
    priority: ConversationPriority = ConversationPriority.MEDIUM


class ConversationCreate(ConversationBase):
    initial_message: Optional[str] = None


class ConversationUpdate(BaseModel):
    status: Optional[ConversationStatus] = None
    priority: Optional[ConversationPriority] = None
    assigned_to: Optional[str] = None


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    customer_id: str
    status: ConversationStatus
    priority: ConversationPriority
    assigned_to: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    customer: Optional[CustomerOut] = None
    last_message: Optional[MessageOut] = None


class ConversationDetailOut(ConversationOut):
    messages: List[MessageOut] = []


class ConversationListResponse(BaseModel):
    items: List[ConversationOut]
    total: int
    page: int
    limit: int
    pages: int
