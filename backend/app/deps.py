from typing import Annotated

from sqlmodel import Session
from fastapi import Depends, Cookie, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
import jwt

from app.core.db import get_session
from app.services.token import is_token_blacklisted
from app.services.user import get_user_by_id
from app.models.user import User
from app.core.config import settings
from app.core.security import decode_token, verify_token_type
from app.core.exceptions import InvalidTokenException

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_BASE_PATH}/auth/login"
)


async def verify_access_token(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[Session, Depends(get_session)]
) -> dict:
    try:
        payload = decode_token(token)
        if payload is None:
            raise InvalidTokenException(detail="Token has expired or is invalid")
        verify_token_type(payload, "access")
        return payload
    except jwt.exceptions.PyJWTError as e:
        raise InvalidTokenException(detail=f"Invalid token: {str(e)}")


async def verify_refresh_token(
    session: Annotated[Session, Depends(get_session)],
    refresh_token: str | None = Cookie(None, include_in_schema=False)
) -> dict:
    """Verify that the refresh token is valid and not blacklisted"""
    if not refresh_token:
        raise InvalidTokenException()
    
    try:
        payload = decode_token(refresh_token)
        if not payload or not verify_token_type(payload, "refresh"):
            raise InvalidTokenException()
        
        jti = payload.get("jti")
        if jti and is_token_blacklisted(session=session, jti=jti):
            raise InvalidTokenException()
            
        return payload
    except jwt.exceptions.PyJWTError:
        raise InvalidTokenException()


async def get_current_user(
    token_payload: Annotated[dict, Depends(verify_access_token)],
    session: Annotated[Session, Depends(get_session)]
) -> User:
    """Get the current authenticated user"""
    user_id = token_payload.get("sub")
    if not user_id:
        raise InvalidTokenException()
    
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise InvalidTokenException()
    
    user = get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


SessionDep = Annotated[Session, Depends(get_session)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]
TokenPayloadDep = Annotated[dict, Depends(verify_access_token)]
RefreshTokenPayloadDep = Annotated[dict, Depends(verify_refresh_token)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
