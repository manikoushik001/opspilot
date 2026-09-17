from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class BusinessBase(BaseModel):
    name: str
    description: Optional[str] = None
    industry: Optional[str] = "Education"
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    timezone: str = "UTC"


class BusinessCreate(BusinessBase):
    pass


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None


class BusinessOut(BusinessBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
