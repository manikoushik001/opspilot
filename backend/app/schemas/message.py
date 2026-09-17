from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.message import SenderType, MessageIntent


class MessageBase(BaseModel):
    content: str


class MessageCreate(MessageBase):
    sender_type: SenderType = SenderType.STAFF


class CustomerMessageSimulate(MessageBase):
    """Payload when simulating an incoming customer message."""
    pass


class MessageOut(MessageBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    sender_type: SenderType
    sender_id: Optional[str] = None
    intent: Optional[MessageIntent] = None
    ai_confidence: Optional[float] = None
    created_at: datetime
