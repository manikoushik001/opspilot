from typing import AsyncGenerator, Optional, Tuple
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models.membership import BusinessMember, MemberRole
from app.models.business import Business

security = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject missing."
        )

    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive."
        )

    return user


async def get_current_business_membership(
    current_user: User = Depends(get_current_user),
    x_business_id: Optional[str] = Header(None, alias="X-Business-ID"),
    db: AsyncSession = Depends(get_db)
) -> Tuple[User, BusinessMember]:
    """
    Guarantees tenant isolation:
    Verifies that the authenticated user actually belongs to the requested business.
    If no X-Business-ID header is passed, defaults to the user's primary/first business membership.
    """
    stmt = select(BusinessMember).where(BusinessMember.user_id == current_user.id)
    if x_business_id:
        stmt = stmt.where(BusinessMember.business_id == x_business_id)

    res = await db.execute(stmt)
    membership = res.scalars().first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not an authorized member of this business tenant."
        )

    return current_user, membership


async def require_owner_role(
    auth_data: Tuple[User, BusinessMember] = Depends(get_current_business_membership)
) -> Tuple[User, BusinessMember]:
    user, membership = auth_data
    if membership.role != MemberRole.OWNER and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Business OWNER role required for this operation."
        )
    return user, membership
