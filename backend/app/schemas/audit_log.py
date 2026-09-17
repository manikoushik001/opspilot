from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    user_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    metadata_dict: Dict[str, Any] = {}
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: List[AuditLogOut]
    total: int
    page: int
    limit: int
