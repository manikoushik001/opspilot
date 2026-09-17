from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.business import Business
from app.schemas.business import BusinessUpdate
from app.services.audit_service import AuditService


class BusinessService:
    @staticmethod
    async def get_business(db: AsyncSession, business_id: str) -> Business:
        stmt = select(Business).where(Business.id == business_id)
        res = await db.execute(stmt)
        business = res.scalar_one_or_none()
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found."
            )
        return business

    @staticmethod
    async def update_business(
        db: AsyncSession,
        business_id: str,
        update_data: BusinessUpdate,
        user_id: str
    ) -> Business:
        business = await BusinessService.get_business(db, business_id)

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, val in update_dict.items():
            setattr(business, key, val)

        await db.flush()

        await AuditService.log_action(
            db=db,
            business_id=business_id,
            action="BUSINESS_UPDATED",
            resource_type="business",
            resource_id=business_id,
            user_id=user_id,
            metadata=update_dict
        )

        return business
