from datetime import timedelta

from fastapi import (
    APIRouter, 
    HTTPException, 
    status, 
    Depends, 
    Response, 
    Cookie, 
    Request
)
from sqlmodel import Session
from jose import JWTError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
)
from app.core.exceptions import InvalidCredentialsException, InvalidTokenException
from app.core.config import settings
from app.services.user import get_user_by_email, create_user, authenticate_user
from app.deps import get_session, SessionDep
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
    
    # Check if username already exists
    from app.services.user import get_user_by_username
    if existing_user := get_user_by_username(session=session, username=user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user (password hashing is handled in create_user)
    user = create_user(session=session, user=user_data)
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Set refresh token cookie
    set_refresh_token_cookie(response, refresh_token)
    
    return Token(access_token=access_token)

@router.post("/login", response_model=Token)
async def login(
    response: Response,
    credentials: UserLogin,
    session: Session = Depends(get_session)
) -> Token:
    try:
        # Authenticate user (will raise InvalidCredentialsException if credentials are invalid)
        user = authenticate_user(
            session=session,
            email=credentials.email,
            username=credentials.username,
            password=credentials.password
        )
        
        # Generate tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Set refresh token cookie
        set_refresh_token_cookie(response, refresh_token)
        
        return Token(access_token=access_token)
    
    except InvalidCredentialsException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    response: Response,
    session: SessionDep,
    refresh_token: str | None = Cookie(None, include_in_schema=False)
) -> Token:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )
    
    try:
        payload = decode_token(refresh_token)
        verify_token_type(payload, "refresh")
        
        # Check if token is blacklisted
        from app.services.token import is_token_blacklisted
        from app.core.security import get_token_jti
        
        jti = get_token_jti(payload)
        if jti and is_token_blacklisted(session=session, jti=jti):
            raise InvalidTokenException()
        
        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenException()
        
        # Generate new tokens
        access_token = create_access_token(data={"sub": user_id})
        new_refresh_token = create_refresh_token(data={"sub": user_id})
        
        # Blacklist the old refresh token
        from app.services.token import blacklist_token
        blacklist_token(session=session, token=refresh_token)
        
        # Set new refresh token cookie
        set_refresh_token_cookie(response, new_refresh_token)
        
        return Token(access_token=access_token)
        
    except (InvalidTokenException, JWTError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/logout")
async def logout(
    response: Response,
    session: Session,
    refresh_token: str | None = Cookie(None, include_in_schema=False)
):
    """Blacklist refresh token and clear refresh token cookie"""
    secure_cookie = settings.ENVIRONMENT == "production"
    samesite = "lax" if settings.ENVIRONMENT == "development" else "strict"
    
    # Blacklist the refresh token if present
    if refresh_token:
        from app.services.token import blacklist_token
        blacklist_token(session=session, token=refresh_token)
    
    # Clear refresh token cookie
    response.delete_cookie(
        key="refresh_token",
        secure=secure_cookie,
        samesite=samesite,
        httponly=True
    )
    
    return {"message": "Successfully logged out"}