from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.followup import Followup, FollowupStatus
from app.models.customer import Customer
from app.schemas.followup import FollowupCreate, FollowupUpdate, FollowupListResponse
from app.services.audit_service import AuditService


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class FollowupService:
    @staticmethod
    async def list_followups(
        db: AsyncSession,
        business_id: str,
        status_filter: Optional[FollowupStatus] = None,
        only_overdue: bool = False
    ) -> FollowupListResponse:
        now = datetime.now(timezone.utc)
        base_query = (
            select(Followup)
            .where(Followup.business_id == business_id)
            .options(selectinload(Followup.customer))
        )

        if status_filter:
            base_query = base_query.where(Followup.status == status_filter)

        if only_overdue:
            base_query = base_query.where(
                and_(
                    Followup.status == FollowupStatus.PENDING,
                    Followup.due_at < now
                )
            )

        stmt = base_query.order_by(Followup.due_at.asc())
        res = await db.execute(stmt)
        items = res.scalars().all()

        # Compute counts
        all_stmt = select(Followup).where(Followup.business_id == business_id)
        all_res = await db.execute(all_stmt)
        all_items = all_res.scalars().all()

        pending_count = sum(1 for f in all_items if f.status == FollowupStatus.PENDING)
        completed_count = sum(1 for f in all_items if f.status == FollowupStatus.COMPLETED)
        overdue_count = sum(1 for f in all_items if f.status == FollowupStatus.PENDING and _ensure_utc(f.due_at) < now)

        # Annotate overdue on items
        for f in items:
            f.is_overdue = bool(f.status == FollowupStatus.PENDING and _ensure_utc(f.due_at) < now)

        return FollowupListResponse(
            items=items,
            total=len(items),
            pending_count=pending_count,
            overdue_count=overdue_count,
            completed_count=completed_count
        )

    @staticmethod
    async def get_followup(db: AsyncSession, business_id: str, followup_id: str) -> Followup:
        stmt = (
            select(Followup)
            .where(
                Followup.id == followup_id,
                Followup.business_id == business_id
            )
            .options(selectinload(Followup.customer))
        )
        res = await db.execute(stmt)
        followup = res.scalar_one_or_none()
        if not followup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Follow-up task not found."
            )
        now = datetime.now(timezone.utc)
        followup.is_overdue = bool(followup.status == FollowupStatus.PENDING and _ensure_utc(followup.due_at) < now)
        return followup

    @staticmethod
    async def create_followup(
        db: AsyncSession,
        business_id: str,
        user_id: str,
        followup_in: FollowupCreate
    ) -> Followup:
        # Verify customer
        cust_stmt = select(Customer).where(
            Customer.id == followup_in.customer_id,
            Customer.business_id == business_id
        )
        cust_res = await db.execute(cust_stmt)
        if not cust_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found in this business."
            )

        followup = Followup(
            business_id=business_id,
            customer_id=followup_in.customer_id,
            conversation_id=followup_in.conversation_id,
            assigned_to=followup_in.assigned_to or user_id,
            title=followup_in.title,
            description=followup_in.description,
            due_at=followup_in.due_at,
            status=FollowupStatus.PENDING
        )
        db.add(followup)
        await db.flush()

        await AuditService.log_action(
            db=db,
            business_id=business_id,
            action="FOLLOWUP_CREATED",
            resource_type="followup",
            resource_id=followup.id,
            user_id=user_id,
            metadata={"title": followup.title, "due_at": followup.due_at.isoformat()}
        )
        return await FollowupService.get_followup(db, business_id, followup.id)

    @staticmethod
    async def update_followup(
        db: AsyncSession,
        business_id: str,
        followup_id: str,
        user_id: str,
        followup_in: FollowupUpdate
    ) -> Followup:
        followup = await FollowupService.get_followup(db, business_id, followup_id)
        update_dict = followup_in.model_dump(exclude_unset=True)

        for k, v in update_dict.items():
            setattr(followup, k, v)

        if followup_in.status == FollowupStatus.COMPLETED:
            followup.completed_at = datetime.now(timezone.utc)
            await AuditService.log_action(
                db=db,
                business_id=business_id,
                action="FOLLOWUP_COMPLETED",
                resource_type="followup",
                resource_id=followup.id,
                user_id=user_id
            )
        else:
            await AuditService.log_action(
                db=db,
                business_id=business_id,
                action="FOLLOWUP_UPDATED",
                resource_type="followup",
                resource_id=followup.id,
                user_id=user_id,
                metadata=update_dict
            )

        await db.flush()
        return followup
