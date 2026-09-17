from typing import Tuple, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerOut, CustomerListResponse
from app.models.customer import CustomerStatus
from app.models.user import User
from app.models.membership import BusinessMember
from app.services.customer_service import CustomerService
from app.api.deps import get_current_business_membership

router = APIRouter()


@router.get("", response_model=CustomerListResponse)
async def list_customers(
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    status: Optional[CustomerStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    return await CustomerService.list_customers(
        db=db,
        business_id=membership.business_id,
        search=search,
        status_filter=status,
        page=page,
        limit=limit
    )


@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_in: CustomerCreate,
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    return await CustomerService.create_customer(
        db=db,
        business_id=membership.business_id,
        user_id=user.id,
        customer_in=customer_in
    )


@router.get("/{customer_id}", response_model=CustomerOut)
async def get_customer(
    customer_id: str,
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    return await CustomerService.get_customer(
        db=db,
        business_id=membership.business_id,
        customer_id=customer_id
    )


@router.patch("/{customer_id}", response_model=CustomerOut)
async def update_customer(
    customer_id: str,
    customer_in: CustomerUpdate,
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    return await CustomerService.update_customer(
        db=db,
        business_id=membership.business_id,
        customer_id=customer_id,
        user_id=user.id,
        customer_in=customer_in
    )


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: str,
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership),
    db: AsyncSession = Depends(get_db)
):
    user, membership = auth_data
    await CustomerService.delete_customer(
        db=db,
        business_id=membership.business_id,
        customer_id=customer_id,
        user_id=user.id
    )
    return None
