from datetime import datetime, timezone, timedelta
from typing import Tuple, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.schemas.ai import (
    AIClassifyRequest, AIClassifyResponse,
    AIAnswerRequest, AIAnswerResponse,
    AISuggestActionRequest, AISuggestActionResponse,
    AIActionExecuteRequest, AIActionOut
)
from app.models.user import User
from app.models.membership import BusinessMember
from app.models.business import Business
from app.models.customer import Customer, CustomerStatus
from app.models.conversation import Conversation, ConversationStatus
from app.models.followup import Followup, FollowupStatus
from app.models.ai_action import AIAction, ActionType, ActionExecutionStatus
from app.ai.service import AIService
from app.services.conversation_service import ConversationService
from app.services.audit_service import AuditService
from app.api.deps import get_current_business_membership

router = APIRouter()


@router.post("/classify", response_model=AIClassifyResponse)
async def classify_message_intent(
    req: AIClassifyRequest,
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    ai_svc = AIService(db)
    res = await ai_svc.classify_intent(
        text=req.text,
        business_id=membership.business_id
    )
    return AIClassifyResponse(
        intent=res["intent"],
        confidence=res["confidence"],
        model=res["model"],
        is_injection_suspected=res["is_injection_suspected"],
        requires_human_escalation=res["requires_human_escalation"],
        reasoning=res["reasoning"]
    )


@router.post("/answer", response_model=AIAnswerResponse)
async def generate_rag_answer(
    req: AIAnswerRequest,
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    conv = await ConversationService.get_conversation(db, membership.business_id, req.conversation_id)

    biz_stmt = select(Business).where(Business.id == membership.business_id)
    biz_res = await db.execute(biz_stmt)
    biz = biz_res.scalar_one_or_none()
    biz_name = biz.name if biz else "Business"

    ai_svc = AIService(db)
    res = await ai_svc.generate_grounded_answer(
        business_id=membership.business_id,
        business_name=biz_name,
        conversation_id=conv.id,
        customer_message=req.message
    )

    return AIAnswerResponse(
        answer=res["answer"],
        confidence=res["confidence"],
        intent=res["intent"],
        sources_used=res["sources_used"],
        is_escalated=res["is_escalated"],
        escalation_reason=res["escalation_reason"],
        suggested_action=res["suggested_action"],
        action_payload=res["action_payload"],
        latency_ms=res["latency_ms"]
    )


@router.post("/suggest-action", response_model=AISuggestActionResponse)
async def suggest_action(
    req: AISuggestActionRequest,
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    await ConversationService.get_conversation(db, membership.business_id, req.conversation_id)

    ai_svc = AIService(db)
    res = await ai_svc.provider.suggest_action(
        message=req.message,
        intent=req.intent.value if req.intent else "OTHER"
    )

    action_enum = ActionType(res.get("action", "NONE"))
    return AISuggestActionResponse(
        action=action_enum,
        confidence=res.get("confidence", 0.85),
        reason=res.get("reason", "Suggested action"),
        payload=res.get("payload", {})
    )


@router.post("/execute-action", response_model=Dict[str, Any])
async def execute_proposed_action(
    req: AIActionExecuteRequest,
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    """
    Validates and executes an AI-proposed action under strict tenant isolation.
    """
    user, membership = auth_data
    business_id = membership.business_id

    # 1. Verify conversation and customer exist and belong to business
    conv = await ConversationService.get_conversation(db, business_id, req.conversation_id)
    cust_stmt = select(Customer).where(Customer.id == req.customer_id, Customer.business_id == business_id)
    cust_res = await db.execute(cust_stmt)
    customer = cust_res.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found in this business.")

    action_record = None
    if req.action_id:
        act_stmt = select(AIAction).where(AIAction.id == req.action_id, AIAction.business_id == business_id)
        act_res = await db.execute(act_stmt)
        action_record = act_res.scalar_one_or_none()

    execution_msg = ""

    if req.action_type == ActionType.CREATE_FOLLOWUP:
        due_days = req.payload.get("due_days", 1)
        due_at = datetime.now(timezone.utc) + timedelta(days=due_days)
        title = req.payload.get("title", f"Follow up with {customer.name}")

        followup = Followup(
            business_id=business_id,
            customer_id=customer.id,
            conversation_id=conv.id,
            assigned_to=user.id,
            title=title,
            description=req.payload.get("description", "Created from AI action proposal"),
            due_at=due_at,
            status=FollowupStatus.PENDING
        )
        db.add(followup)
        execution_msg = f"Created Follow-up task '{title}' due on {due_at.strftime('%Y-%m-%d')}."

    elif req.action_type == ActionType.ESCALATE_TO_HUMAN:
        conv.status = ConversationStatus.HUMAN_REVIEW
        execution_msg = "Conversation escalated to human review status."

    elif req.action_type == ActionType.UPDATE_CUSTOMER_STATUS:
        new_status_str = req.payload.get("new_status", "ACTIVE")
        try:
            new_status = CustomerStatus(new_status_str)
            customer.status = new_status
            execution_msg = f"Customer status updated to {new_status.value}."
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid customer status: {new_status_str}")
    else:
        execution_msg = "No action executed."

    if action_record:
        action_record.status = ActionExecutionStatus.EXECUTED
        action_record.execution_result = execution_msg

    await db.flush()

    await AuditService.log_action(
        db=db,
        business_id=business_id,
        action="AI_ACTION_EXECUTED",
        resource_type="ai_action",
        resource_id=req.action_id or conv.id,
        user_id=user.id,
        metadata={"action_type": req.action_type.value, "result": execution_msg}
    )

    return {
        "success": True,
        "action_type": req.action_type.value,
        "result": execution_msg
    }
