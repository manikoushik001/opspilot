from typing import List, Dict
from pydantic import BaseModel


class IntentCount(BaseModel):
    intent: str
    count: int
    percentage: float


class VolumePoint(BaseModel):
    date: str
    total_conversations: int
    ai_handled: int
    human_escalated: int


class ResolutionMethodBreakdown(BaseModel):
    ai_resolved: int
    human_resolved: int
    open_or_in_progress: int
    escalated_to_human: int


class AnalyticsOverviewResponse(BaseModel):
    total_customers: int
    total_conversations: int
    open_conversations: int
    resolved_conversations: int
    human_escalations: int
    pending_followups: int
    overdue_followups: int
    ai_resolution_rate: float
    avg_response_time_seconds: float
    avg_ai_confidence: float
    intent_distribution: List[IntentCount] = []
    daily_volume: List[VolumePoint] = []
    resolution_breakdown: ResolutionMethodBreakdown
