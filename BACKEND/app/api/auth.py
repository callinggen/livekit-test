from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
import random
import string

from app.database import get_db
from app.models.user import User
from app.models.password_reset import PasswordReset
from app.schemas.auth import LoginRequest, Token, ForgotPasswordRequest, VerifyResetCodeRequest, ResetPasswordRequest
from app.core.security import verify_password, create_access_token, get_password_hash
from app.services.email_service import email_service

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
        "full_name": user.full_name,
    }

@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
):
    # Check if user exists
    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        # Don't reveal that the user doesn't exist
        return {"message": "If that email exists, a reset code has been sent."}
        
    # Generate 6-digit code
    reset_code = ''.join(random.choices(string.digits, k=6))
    
    # Save to DB
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    
    # Delete any existing codes for this email
    # For simplicity, we just add a new one and verify the latest unexpired one later
    
    reset_entry = PasswordReset(
        email=data.email,
        reset_code=reset_code,
        expires_at=expires_at
    )
    db.add(reset_entry)
    await db.commit()
    
    # Send email
    try:
        # Pass to background task ideally, but for now we do it synchronously
        email_service.send_password_reset_email(data.email, reset_code)
    except Exception as e:
        print(f"Email sending failed: {e}")
        # We don't fail the request so the user doesn't know what happened internally
        
    return {"message": "If that email exists, a reset code has been sent."}

@router.post("/verify-reset-code")
async def verify_reset_code(
    data: VerifyResetCodeRequest, db: AsyncSession = Depends(get_db)
):
    stmt = select(PasswordReset).where(
        PasswordReset.email == data.email,
        PasswordReset.reset_code == data.reset_code,
        PasswordReset.expires_at > datetime.utcnow()
    )
    result = await db.execute(stmt)
    reset_entry = result.scalars().first()
    
    if not reset_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code."
        )
        
    return {"message": "Code verified."}

@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
):
    # Verify code again
    stmt = select(PasswordReset).where(
        PasswordReset.email == data.email,
        PasswordReset.reset_code == data.reset_code,
        PasswordReset.expires_at > datetime.utcnow()
    )
    result = await db.execute(stmt)
    reset_entry = result.scalars().first()
    
    if not reset_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code."
        )
        
    # Find user
    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found."
        )
        
    # Update password
    user.hashed_password = get_password_hash(data.new_password)
    
    # Delete the reset entry so it can't be reused
    await db.delete(reset_entry)
    
    await db.commit()
    
    return {"message": "Password reset successfully."}
