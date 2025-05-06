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

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
)
from app.deps import get_session, SessionDep, CurrentUserDep
from app.schemas.user import UserCreate, UserLogin, UserPublic
from app.services import (
    user as user_service,
    token as token_service
)
from app.schemas.token import Token, AuthResponse
from app.core.config import settings
from app.core.exceptions import (
    InvalidCredentialsException, 
    InvalidTokenException, 
    InvalidPasswordException,
    DuplicateEmailException,
    DuplicateUsernameException,
)

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


@router.get("/me", response_model=UserPublic)
async def get_current_user(current_user: CurrentUserDep) -> UserPublic:
    """Get current authenticated user"""
    return current_user


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    response: Response,
    user_data: UserCreate,
    session: Session = Depends(get_session)
) -> AuthResponse:
    try:
        # Check if email already exists
        if existing_user := user_service.get_user_by_email(session=session, email=user_data.email):
            raise DuplicateEmailException()
        
        # Check if username already exists
        if existing_user := user_service.get_user_by_username(session=session, username=user_data.username):
            raise DuplicateUsernameException()
        
        user = user_service.create_user(session=session, user=user_data)
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        
        set_refresh_token_cookie(response, refresh_token)
        token = Token(access_token=access_token)

        return AuthResponse(token=token, user=user)
    except InvalidPasswordException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail)
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    response: Response,
    credentials: UserLogin,
    session: Session = Depends(get_session)
) -> AuthResponse:
    user = user_service.authenticate_user(
        session=session,
        email=credentials.email,
        username=credentials.username,
        password=credentials.password
    )

    if not user:
        raise InvalidCredentialsException()
    
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    set_refresh_token_cookie(response, refresh_token)
    token = Token(access_token=access_token)
    
    return AuthResponse(token=token, user=user)


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    request: Request,
    response: Response,
    session: SessionDep,
    refresh_token: str | None = Cookie(None, include_in_schema=False)
) -> AuthResponse:
    if not refresh_token:
        raise InvalidTokenException()
    
    payload = decode_token(refresh_token)
    if not payload or not verify_token_type(payload, "refresh"):
        raise InvalidTokenException()

    jti, user_id = payload.get("jti"), payload.get("sub")
    if not jti or not user_id:
        raise InvalidTokenException()

    if token_service.is_token_blacklisted(session=session, jti=jti):
        raise InvalidTokenException()
    
    user = user_service.get_user_by_id(session=session, user_id=int(user_id))
    if not user:
        raise InvalidTokenException()
    
    access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)
    
    # Blacklist the old refresh token
    token_service.blacklist_token(session=session, token=refresh_token)

    set_refresh_token_cookie(response, new_refresh_token)
    token = Token(access_token=access_token)
    
    return AuthResponse(token=token, user=user)


@router.post("/logout")
async def logout(
    response: Response,
    session: SessionDep,
    refresh_token: str | None = Cookie(None, include_in_schema=False)
):
    if refresh_token:
        token_service.blacklist_token(session=session, token=refresh_token)
    
    secure_cookie = settings.ENVIRONMENT == "production"
    samesite = "lax" if settings.ENVIRONMENT == "development" else "strict"

    response.delete_cookie(
        key="refresh_token",
        secure=secure_cookie,
        samesite=samesite,
        httponly=True
    )
    
    return { "message": "Successfully logged out" }
