import enum
import json
from sqlalchemy import Column, String, Text, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ActionType(str, enum.Enum):
    CREATE_FOLLOWUP = "CREATE_FOLLOWUP"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"
    UPDATE_CUSTOMER_STATUS = "UPDATE_CUSTOMER_STATUS"
    NONE = "NONE"


class ActionExecutionStatus(str, enum.Enum):
    PROPOSED = "PROPOSED"
    VALIDATED = "VALIDATED"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"


class AIAction(BaseModel):
    __tablename__ = "ai_actions"
    __table_args__ = (
        Index("ix_ai_actions_business_status", "business_id", "status"),
    )

    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    action_type = Column(Enum(ActionType), default=ActionType.NONE, nullable=False)
    status = Column(Enum(ActionExecutionStatus), default=ActionExecutionStatus.PROPOSED, nullable=False)
    reason = Column(Text, nullable=True)
    payload_json = Column(Text, nullable=True)
    execution_result = Column(Text, nullable=True)

    conversation = relationship("Conversation", back_populates="ai_actions")

    @property
    def payload(self):
        if self.payload_json:
            return json.loads(self.payload_json)
        return {}

    @payload.setter
    def payload(self, value):
        if value is not None:
            self.payload_json = json.dumps(value)
        else:
            self.payload_json = "{}"
