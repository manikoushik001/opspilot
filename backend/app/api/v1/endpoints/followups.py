from typing import Tuple, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.followup import FollowupCreate, FollowupUpdate, FollowupOut, FollowupListResponse
from app.models.followup import FollowupStatus
from app.models.user import User
from app.models.membership import BusinessMember
from app.services.followup_service import FollowupService
from app.api.deps import get_current_business_membership

router = APIRouter()


@router.get("", response_model=FollowupListResponse)
async def list_followups(
    status: Optional[FollowupStatus] = Query(None, description="Filter by status"),
    overdue: bool = Query(False, description="Filter overdue tasks"),
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    return await FollowupService.list_followups(
        db=db,
        business_id=membership.business_id,
        status_filter=status,
        only_overdue=overdue
    )


@router.post("", response_model=FollowupOut, status_code=status.HTTP_201_CREATED)
async def create_followup(
    followup_in: FollowupCreate,
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    return await FollowupService.create_followup(
        db=db,
        business_id=membership.business_id,
        user_id=user.id,
        followup_in=followup_in
    )


@router.get("/{followup_id}", response_model=FollowupOut)
async def get_followup(
    followup_id: str,
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    return await FollowupService.get_followup(
        db=db,
        business_id=membership.business_id,
        followup_id=followup_id
    )


@router.patch("/{followup_id}", response_model=FollowupOut)
async def update_followup(
    followup_id: str,
    followup_in: FollowupUpdate,
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    return await FollowupService.update_followup(
        db=db,
        business_id=membership.business_id,
        followup_id=followup_id,
        user_id=user.id,
        followup_in=followup_in
    )
