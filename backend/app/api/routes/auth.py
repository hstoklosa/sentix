from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Response, Cookie, Request
from sqlmodel import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
)
from app.core.config import settings
from app.services.user import get_user_by_email, create_user, authenticate_user
from app.deps import get_session
from app.schemas.user import UserCreate, UserLogin
from app.schemas.token import Token

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

def set_refresh_token_cookie(response: Response, refresh_token: str):
    """Helper function to consistently set refresh token cookie"""
    secure_cookie = settings.ENVIRONMENT == "production"
    samesite = "lax" if settings.ENVIRONMENT == "development" else "strict"
    max_age = int(timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES).total_seconds())
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure_cookie,
        samesite=samesite,
        max_age=max_age
    )

@router.post("/register", response_model=Token)
async def register(
    response: Response,
    user_data: UserCreate,
    session: Session = Depends(get_session)
) -> Token:
    # Check if user already exists
    if existing_user := get_user_by_email(session=session, email=user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user (password hashing is handled in create_user)
    user = create_user(session=session, user=user_data)
    
    # Generate tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    # Set refresh token cookie
    set_refresh_token_cookie(response, refresh_token)
    
    return Token(access_token=access_token)

@router.post("/login", response_model=Token)
async def login(
    response: Response,
    credentials: UserLogin,
    session: Session = Depends(get_session)
) -> Token:
    # Authenticate user (will raise InvalidCredentialsException if credentials are invalid)
    user = authenticate_user(
        session=session,
        email=credentials.email,
        password=credentials.password
    )
    
    # Generate tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    # Set refresh token cookie
    set_refresh_token_cookie(response, refresh_token)
    
    return Token(access_token=access_token)

@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    response: Response,
    refresh_token: str | None = Cookie(None, include_in_schema=False),
    session: Session = Depends(get_session)
) -> Token:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )
    
    try:
        payload = decode_token(refresh_token)
        verify_token_type(payload, "refresh")
        
        # Generate new tokens
        access_token = create_access_token(subject=payload["sub"])
        new_refresh_token = create_refresh_token(subject=payload["sub"])
        
        # Set new refresh token cookie
        set_refresh_token_cookie(response, new_refresh_token)
        
        return Token(access_token=access_token)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(None, include_in_schema=False)
):
    """Clear refresh token cookie"""
    secure_cookie = settings.ENVIRONMENT == "production"
    samesite = "lax" if settings.ENVIRONMENT == "development" else "strict"
    
    # Even if no refresh token is present, we clear it
    response.delete_cookie(
        key="refresh_token",
        secure=secure_cookie,
        samesite=samesite,
        httponly=True
    )
    
    return {"message": "Successfully logged out"}
