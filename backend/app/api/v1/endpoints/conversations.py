from typing import Tuple, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.conversation import (
    ConversationCreate, ConversationUpdate, ConversationOut,
    ConversationDetailOut, ConversationListResponse
)
from app.models.conversation import ConversationStatus, ConversationPriority
from app.models.user import User
from app.models.membership import BusinessMember
from app.services.conversation_service import ConversationService
from app.api.deps import get_current_business_membership

router = APIRouter()


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    status: Optional[ConversationStatus] = Query(None, description="Filter by status"),
    priority: Optional[ConversationPriority] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search customer name or email"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    return await ConversationService.list_conversations(
        db=db,
        business_id=membership.business_id,
        status_filter=status,
        priority_filter=priority,
        search=search,
        page=page,
        limit=limit
    )


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conv_in: ConversationCreate,
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    return await ConversationService.create_conversation(
        db=db,
        business_id=membership.business_id,
        user_id=user.id,
        conv_in=conv_in
    )


@router.get("/{conversation_id}", response_model=ConversationDetailOut)
async def get_conversation(
    conversation_id: str,
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    return await ConversationService.get_conversation(
        db=db,
        business_id=membership.business_id,
        conversation_id=conversation_id
    )


@router.patch("/{conversation_id}", response_model=ConversationOut)
async def update_conversation(
    conversation_id: str,
    conv_in: ConversationUpdate,
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    return await ConversationService.update_conversation(
        db=db,
        business_id=membership.business_id,
        conversation_id=conversation_id,
        user_id=user.id,
        conv_in=conv_in
    )
