import math
from typing import Tuple
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.schemas.audit_log import AuditLogListResponse, AuditLogOut
from app.models.audit_log import AuditLog
from app.models.user import User
from app.models.membership import BusinessMember
from app.api.deps import require_owner_role

router = APIRouter()


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    auth_data: Tuple[User, BusinessMember] = Depends(require_owner_role),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data

    count_stmt = select(func.count(AuditLog.id)).where(AuditLog.business_id == membership.business_id)
    count_res = await db.execute(count_stmt)
    total = count_res.scalar_one() or 0

    offset = (page - 1) * limit
    stmt = (
        select(AuditLog)
        .where(AuditLog.business_id == membership.business_id)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    res = await db.execute(stmt)
    logs = res.scalars().all()

    return AuditLogListResponse(
        items=logs,
        total=total,
        page=page,
        limit=limit
    )
