from typing import Tuple
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.business import BusinessOut, BusinessUpdate
from app.models.user import User
from app.models.membership import BusinessMember
from app.services.business_service import BusinessService
from app.api.deps import get_current_business_membership, require_owner_role

router = APIRouter()


@router.get("", response_model=BusinessOut)
async def get_current_business(
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    return await BusinessService.get_business(db, membership.business_id)


@router.patch("", response_model=BusinessOut)
async def update_business(
    business_in: BusinessUpdate,
    auth_data: Tuple[User, BusinessMember] = Depends(require_owner_role),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    return await BusinessService.update_business(db, membership.business_id, business_in, user.id)
