from datetime import datetime, timezone
import math
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.conversation import Conversation, ConversationStatus, ConversationPriority
from app.models.customer import Customer
from app.models.message import Message, SenderType, MessageIntent
from app.models.business import Business
from app.models.followup import Followup, FollowupStatus
from app.schemas.conversation import ConversationCreate, ConversationUpdate, ConversationListResponse
from app.services.audit_service import AuditService
from app.ai.service import AIService
from app.core.logging import get_logger

logger = get_logger("conversation.service")


class ConversationService:
    @staticmethod
    async def list_conversations(
        db: AsyncSession,
        business_id: str,
        status_filter: Optional[ConversationStatus] = None,
        priority_filter: Optional[ConversationPriority] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> ConversationListResponse:
        base_query = (
            select(Conversation)
            .where(Conversation.business_id == business_id)
            .options(selectinload(Conversation.customer))
        )

        if status_filter:
            base_query = base_query.where(Conversation.status == status_filter)

        if priority_filter:
            base_query = base_query.where(Conversation.priority == priority_filter)

        if search:
            term = f"%{search}%"
            base_query = base_query.join(Customer).where(
                or_(
                    Customer.name.ilike(term),
                    Customer.email.ilike(term),
                    Customer.phone.ilike(term)
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(base_query.subquery())
        count_res = await db.execute(count_stmt)
        total = count_res.scalar_one() or 0

        # Paginate
        offset = (page - 1) * limit
        stmt = base_query.order_by(Conversation.updated_at.desc()).offset(offset).limit(limit)
        res = await db.execute(stmt)
        items = res.scalars().all()

        # Load last message for each conversation
        for conv in items:
            msg_stmt = (
                select(Message)
                .where(Message.conversation_id == conv.id)
                .order_by(Message.created_at.desc())
                .limit(1)
            )
            msg_res = await db.execute(msg_stmt)
            conv.last_message = msg_res.scalar_one_or_none()

        pages = math.ceil(total / limit) if total > 0 else 1

        return ConversationListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=pages
        )

    @staticmethod
    async def get_conversation(
        db: AsyncSession,
        business_id: str,
        conversation_id: str
    ) -> Conversation:
        stmt = (
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.business_id == business_id
            )
            .options(
                selectinload(Conversation.customer),
                selectinload(Conversation.messages)
            )
        )
        res = await db.execute(stmt)
        conversation = res.scalar_one_or_none()
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found in this business."
            )
        return conversation

    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        business_id: str,
        user_id: str,
        conv_in: ConversationCreate
    ) -> Conversation:
        # Verify customer belongs to this business
        cust_stmt = select(Customer).where(
            Customer.id == conv_in.customer_id,
            Customer.business_id == business_id
        )
        cust_res = await db.execute(cust_stmt)
        if not cust_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found in this business."
            )

        conv = Conversation(
            business_id=business_id,
            customer_id=conv_in.customer_id,
            status=ConversationStatus.OPEN,
            priority=conv_in.priority
        )
        db.add(conv)
        await db.flush()

        if conv_in.initial_message:
            msg = Message(
                conversation_id=conv.id,
                sender_type=SenderType.CUSTOMER,
                sender_id=conv_in.customer_id,
                content=conv_in.initial_message
            )
            db.add(msg)
            await db.flush()

        await AuditService.log_action(
            db=db,
            business_id=business_id,
            action="CONVERSATION_CREATED",
            resource_type="conversation",
            resource_id=conv.id,
            user_id=user_id
        )
        return await ConversationService.get_conversation(db, business_id, conv.id)

    @staticmethod
    async def update_conversation(
        db: AsyncSession,
        business_id: str,
        conversation_id: str,
        user_id: str,
        conv_in: ConversationUpdate
    ) -> Conversation:
        conv = await ConversationService.get_conversation(db, business_id, conversation_id)
        update_dict = conv_in.model_dump(exclude_unset=True)

        for k, v in update_dict.items():
            setattr(conv, k, v)

        if conv_in.status == ConversationStatus.RESOLVED:
            conv.resolved_at = datetime.now(timezone.utc)

        await db.flush()

        await AuditService.log_action(
            db=db,
            business_id=business_id,
            action="CONVERSATION_UPDATED",
            resource_type="conversation",
            resource_id=conversation_id,
            user_id=user_id,
            metadata=update_dict
        )
        return conv

    @staticmethod
    async def add_staff_message(
        db: AsyncSession,
        business_id: str,
        conversation_id: str,
        user_id: str,
        content: str
    ) -> Message:
        conv = await ConversationService.get_conversation(db, business_id, conversation_id)

        msg = Message(
            conversation_id=conv.id,
            sender_type=SenderType.STAFF,
            sender_id=user_id,
            content=content
        )
        db.add(msg)
        conv.updated_at = datetime.now(timezone.utc)
        if conv.status == ConversationStatus.HUMAN_REVIEW:
            conv.status = ConversationStatus.OPEN

        await db.flush()

        await AuditService.log_action(
            db=db,
            business_id=business_id,
            action="MESSAGE_SENT",
            resource_type="message",
            resource_id=msg.id,
            user_id=user_id,
            metadata={"sender": "STAFF", "conversation_id": conv.id}
        )
        return msg

    @staticmethod
    async def process_customer_message(
        db: AsyncSession,
        business_id: str,
        conversation_id: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Processes an incoming customer message through the AI RAG Pipeline:
        1. Saves customer message to history
        2. Classifies intent & checks prompt injection
        3. Retrieves grounded context from knowledge base
        4. Generates AI response or triggers human escalation
        5. Proposes AI action (e.g. follow-up task)
        6. Updates conversation state
        """
        conv = await ConversationService.get_conversation(db, business_id, conversation_id)
        biz_stmt = select(Business).where(Business.id == business_id)
        biz_res = await db.execute(biz_stmt)
        biz = biz_res.scalar_one_or_none()
        biz_name = biz.name if biz else "OpsPilot"

        ai_svc = AIService(db)

        # 1. Intent classification
        classify_res = await ai_svc.classify_intent(
            text=content,
            business_id=business_id,
            conversation_id=conversation_id
        )

        # 2. Store customer message with intent metadata
        cust_msg = Message(
            conversation_id=conv.id,
            sender_type=SenderType.CUSTOMER,
            sender_id=conv.customer_id,
            content=content,
            intent=classify_res["intent"],
            ai_confidence=classify_res["confidence"]
        )
        db.add(cust_msg)
        await db.flush()

        # 3. Generate grounded RAG answer
        rag_res = await ai_svc.generate_grounded_answer(
            business_id=business_id,
            business_name=biz_name,
            conversation_id=conversation_id,
            customer_message=content,
            intent=classify_res["intent"]
        )

        # 4. Save AI Response message
        ai_msg = Message(
            conversation_id=conv.id,
            sender_type=SenderType.AI,
            sender_id="ai",
            content=rag_res["answer"],
            intent=classify_res["intent"],
            ai_confidence=rag_res["confidence"]
        )
        db.add(ai_msg)

        # 5. Handle Human Escalation or Status Transitions
        if rag_res["is_escalated"]:
            conv.status = ConversationStatus.HUMAN_REVIEW
            conv.priority = ConversationPriority.HIGH
            await AuditService.log_action(
                db=db,
                business_id=business_id,
                action="AI_ESCALATED",
                resource_type="conversation",
                resource_id=conv.id,
                metadata={"reason": rag_res["escalation_reason"], "intent": str(classify_res["intent"])}
            )
        else:
            conv.status = ConversationStatus.OPEN

        conv.updated_at = datetime.now(timezone.utc)
        await db.flush()

        return {
            "customer_message": cust_msg,
            "ai_response": ai_msg,
            "decision_metadata": {
                "intent": classify_res["intent"].value,
                "confidence": rag_res["confidence"],
                "sources_count": len(rag_res["sources_used"]),
                "sources": rag_res["sources_used"],
                "is_escalated": rag_res["is_escalated"],
                "escalation_reason": rag_res["escalation_reason"],
                "suggested_action": rag_res["suggested_action"].value if rag_res["suggested_action"] else None,
                "action_payload": rag_res["action_payload"],
                "latency_ms": rag_res["latency_ms"]
            }
        }
