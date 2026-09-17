from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from app.core.logging import get_logger

logger = get_logger("audit")


class AuditService:
    @staticmethod
    async def log_action(
        db: AsyncSession,
        business_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        # Sanitize metadata to never persist sensitive values
        sanitized_meta = {}
        if metadata:
            for k, v in metadata.items():
                if any(secret_key in k.lower() for secret_key in ["password", "token", "secret", "key", "authorization"]):
                    sanitized_meta[k] = "[REDACTED]"
                else:
                    sanitized_meta[k] = v

        audit = AuditLog(
            business_id=business_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
        )
        audit.metadata_dict = sanitized_meta
        db.add(audit)
        logger.info(f"[AUDIT] tenant={business_id} action={action} resource={resource_type}:{resource_id} user={user_id}")
        return audit
