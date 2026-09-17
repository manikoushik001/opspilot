from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.message import MessageIntent
from app.models.ai_action import ActionType, ActionExecutionStatus


class AIClassifyRequest(BaseModel):
    text: str


class AIClassifyResponse(BaseModel):
    intent: MessageIntent
    confidence: float
    model: str
    is_injection_suspected: bool = False
    requires_human_escalation: bool = False
    reasoning: Optional[str] = None


class AIAnswerRequest(BaseModel):
    conversation_id: str
    message: str


class AISourceChunk(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    content: str
    similarity_score: float
    chunk_index: int
    page: Optional[int] = None


class AIAnswerResponse(BaseModel):
    answer: str
    confidence: float
    intent: MessageIntent
    sources_used: List[AISourceChunk] = []
    is_escalated: bool = False
    escalation_reason: Optional[str] = None
    suggested_action: Optional[ActionType] = None
    action_payload: Optional[Dict[str, Any]] = None
    latency_ms: int


class AISuggestActionRequest(BaseModel):
    conversation_id: str
    message: str
    intent: Optional[MessageIntent] = None


class AISuggestActionResponse(BaseModel):
    action: ActionType
    confidence: float
    reason: str
    payload: Dict[str, Any] = {}


class AIActionExecuteRequest(BaseModel):
    action_id: Optional[str] = None
    action_type: ActionType
    conversation_id: str
    customer_id: str
    payload: Dict[str, Any] = {}


class AIActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    conversation_id: str
    action_type: ActionType
    status: ActionExecutionStatus
    reason: Optional[str] = None
    payload: Dict[str, Any] = {}
    execution_result: Optional[str] = None
    created_at: datetime


class AIInteractionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    conversation_id: Optional[str] = None
    model: str
    operation: str
    confidence: Optional[float] = None
    retrieval_count: int
    latency_ms: int
    success: bool
    created_at: datetime
