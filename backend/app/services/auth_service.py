from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user import User
from app.models.business import Business
from app.models.membership import BusinessMember, MemberRole
from app.schemas.user import UserCreate, UserLogin, Token
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.services.audit_service import AuditService


class AuthService:
    @staticmethod
    async def register_user(db: AsyncSession, user_in: UserCreate) -> User:
        # Check if user email already exists
        stmt = select(User).where(User.email == user_in.email)
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists."
            )

        # Create user
        user = User(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            is_active=True
        )
        db.add(user)
        await db.flush()

        # Create Default Business
        business_name = user_in.business_name or f"{user_in.full_name}'s Operations"
        business = Business(
            name=business_name,
            industry="Education",
            email=user_in.email
        )
        db.add(business)
        await db.flush()

        # Assign as OWNER
        member = BusinessMember(
            business_id=business.id,
            user_id=user.id,
            role=MemberRole.OWNER
        )
        db.add(member)
        await db.flush()

        # Log audit trail
        await AuditService.log_action(
            db=db,
            business_id=business.id,
            action="USER_REGISTERED",
            resource_type="user",
            resource_id=user.id,
            user_id=user.id,
            metadata={"email": user.email, "role": "OWNER"}
        )

        return user

    @staticmethod
    async def authenticate_user(db: AsyncSession, login_data: UserLogin) -> Token:
        stmt = select(User).where(User.email == login_data.email)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user or not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password."
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive."
            )

        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)

        # Get business membership for audit logging
        mem_stmt = select(BusinessMember).where(BusinessMember.user_id == user.id)
        mem_res = await db.execute(mem_stmt)
        membership = mem_res.scalars().first()
        if membership:
            await AuditService.log_action(
                db=db,
                business_id=membership.business_id,
                action="LOGIN",
                resource_type="auth",
                resource_id=user.id,
                user_id=user.id
            )

        return Token(access_token=access_token, refresh_token=refresh_token)
