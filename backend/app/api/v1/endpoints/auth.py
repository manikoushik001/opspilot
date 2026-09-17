from typing import Tuple, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import decode_token, create_access_token
from app.schemas.user import UserCreate, UserLogin, UserOut, Token, TokenRefreshRequest, BusinessMembershipOut
from app.models.user import User
from app.models.membership import BusinessMember
from app.models.business import Business
from app.services.auth_service import AuthService
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await AuthService.register_user(db, user_in)
    # Reload memberships with business names
    stmt = select(BusinessMember).where(BusinessMember.user_id == user.id).options(selectinload(BusinessMember.business))
    res = await db.execute(stmt)
    memberships = res.scalars().all()

    mem_outs = [
        BusinessMembershipOut(
            business_id=m.business_id,
            business_name=m.business.name if m.business else "Business",
            role=m.role.value
        )
        for m in memberships
    ]
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        memberships=mem_outs
    )


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    return await AuthService.authenticate_user(db, login_data)


@router.post("/refresh", response_model=Token)
async def refresh_token(req: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    refresh = req.refresh_token
    if not refresh:
        raise HTTPException(status_code=400, detail="Missing refresh token.")

    payload = decode_token(refresh)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token.")

    user_id = payload.get("sub")
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive or not found.")

    new_access = create_access_token(subject=user.id)
    return Token(access_token=new_access, refresh_token=refresh)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Successfully logged out."}


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(BusinessMember).where(BusinessMember.user_id == current_user.id).options(selectinload(BusinessMember.business))
    res = await db.execute(stmt)
    memberships = res.scalars().all()

    mem_outs = [
        BusinessMembershipOut(
            business_id=m.business_id,
            business_name=m.business.name if m.business else "Business",
            role=m.role.value
        )
        for m in memberships
    ]
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        memberships=mem_outs
    )
