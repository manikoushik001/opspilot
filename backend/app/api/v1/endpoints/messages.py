from typing import Tuple, List, Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.schemas.message import MessageCreate, CustomerMessageSimulate, MessageOut
from app.models.message import Message
from app.models.user import User
from app.models.membership import BusinessMember
from app.services.conversation_service import ConversationService
from app.api.deps import get_current_business_membership

router = APIRouter()


@router.get("/{conversation_id}/messages", response_model=List[MessageOut])
async def list_messages(
    conversation_id: str,
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    # Check conversation access
    await ConversationService.get_conversation(db, membership.business_id, conversation_id)

    stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/{conversation_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def send_staff_message(
    conversation_id: str,
    msg_in: MessageCreate,
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    return await ConversationService.add_staff_message(
        db=db,
        business_id=membership.business_id,
        conversation_id=conversation_id,
        user_id=user.id,
        content=msg_in.content
    )


@router.post("/{conversation_id}/simulate-customer", status_code=status.HTTP_200_OK)
async def simulate_customer_message(
    conversation_id: str,
    msg_in: CustomerMessageSimulate,
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    user, membership = auth_data
    res = await ConversationService.process_customer_message(
        db=db,
        business_id=membership.business_id,
        conversation_id=conversation_id,
        content=msg_in.content
    )
    return {
        "customer_message": MessageOut.model_validate(res["customer_message"]),
        "ai_response": MessageOut.model_validate(res["ai_response"]),
        "decision_metadata": res["decision_metadata"]
    }
