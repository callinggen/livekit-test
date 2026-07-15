from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, Token
from app.core.security import verify_password, create_access_token

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest, db: AsyncSession = Depends(get_db)
):
    identifier = login_data.identifier
    
    # Try to find user by email first, then by phone_number
    stmt = select(User).where(User.email == identifier)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        stmt = select(User).where(User.phone_number == identifier)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email/phone number or password",
        )
        
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email/phone number or password",
        )
        
    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer",
    }
