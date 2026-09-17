from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    business,
    customers,
    conversations,
    messages,
    knowledge,
    followups,
    ai,
    analytics,
    audit_logs,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(business.router, prefix="/business", tags=["Business"])
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])
api_router.include_router(messages.router, prefix="/conversations", tags=["Messages"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge Base"])
api_router.include_router(followups.router, prefix="/followups", tags=["Follow-ups"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI & RAG Engine"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit Logs"])
