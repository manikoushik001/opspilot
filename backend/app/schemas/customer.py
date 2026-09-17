from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.customer import CustomerStatus


class CustomerBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: CustomerStatus = CustomerStatus.NEW
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[CustomerStatus] = None
    notes: Optional[str] = None


class CustomerOut(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    created_at: datetime
    updated_at: datetime


class CustomerListResponse(BaseModel):
    items: List[CustomerOut]
    total: int
    page: int
    limit: int
    pages: int
