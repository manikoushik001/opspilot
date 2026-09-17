import math
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from fastapi import HTTPException, status

from app.models.customer import Customer, CustomerStatus
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerListResponse
from app.services.audit_service import AuditService


class CustomerService:
    @staticmethod
    async def list_customers(
        db: AsyncSession,
        business_id: str,
        search: Optional[str] = None,
        status_filter: Optional[CustomerStatus] = None,
        page: int = 1,
        limit: int = 20
    ) -> CustomerListResponse:
        base_query = select(Customer).where(Customer.business_id == business_id)

        if status_filter:
            base_query = base_query.where(Customer.status == status_filter)

        if search:
            term = f"%{search}%"
            base_query = base_query.where(
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
        stmt = base_query.order_by(Customer.created_at.desc()).offset(offset).limit(limit)
        res = await db.execute(stmt)
        items = res.scalars().all()

        pages = math.ceil(total / limit) if total > 0 else 1

        return CustomerListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=pages
        )

    @staticmethod
    async def get_customer(
        db: AsyncSession,
        business_id: str,
        customer_id: str
    ) -> Customer:
        stmt = select(Customer).where(
            Customer.id == customer_id,
            Customer.business_id == business_id
        )
        res = await db.execute(stmt)
        customer = res.scalar_one_or_none()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found in this business."
            )
        return customer

    @staticmethod
    async def create_customer(
        db: AsyncSession,
        business_id: str,
        user_id: str,
        customer_in: CustomerCreate
    ) -> Customer:
        customer = Customer(
            business_id=business_id,
            name=customer_in.name,
            email=customer_in.email,
            phone=customer_in.phone,
            status=customer_in.status,
            notes=customer_in.notes
        )
        db.add(customer)
        await db.flush()

        await AuditService.log_action(
            db=db,
            business_id=business_id,
            action="CUSTOMER_CREATED",
            resource_type="customer",
            resource_id=customer.id,
            user_id=user_id,
            metadata={"name": customer.name, "email": customer.email}
        )
        return customer

    @staticmethod
    async def update_customer(
        db: AsyncSession,
        business_id: str,
        customer_id: str,
        user_id: str,
        customer_in: CustomerUpdate
    ) -> Customer:
        customer = await CustomerService.get_customer(db, business_id, customer_id)
        update_dict = customer_in.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(customer, k, v)

        await db.flush()

        await AuditService.log_action(
            db=db,
            business_id=business_id,
            action="CUSTOMER_UPDATED",
            resource_type="customer",
            resource_id=customer.id,
            user_id=user_id,
            metadata=update_dict
        )
        return customer

    @staticmethod
    async def delete_customer(
        db: AsyncSession,
        business_id: str,
        customer_id: str,
        user_id: str
    ) -> bool:
        customer = await CustomerService.get_customer(db, business_id, customer_id)
        await db.delete(customer)
        await db.flush()

        await AuditService.log_action(
            db=db,
            business_id=business_id,
            action="CUSTOMER_DELETED",
            resource_type="customer",
            resource_id=customer_id,
            user_id=user_id
        )
        return True
