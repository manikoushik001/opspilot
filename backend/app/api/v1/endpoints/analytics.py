from typing import Tuple
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.analytics import AnalyticsOverviewResponse
from app.models.user import User
from app.models.membership import BusinessMember
from app.services.analytics_service import AnalyticsService
from app.api.deps import get_current_business_membership

router = APIRouter()


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    return await AnalyticsService.get_overview(db, membership.business_id)
