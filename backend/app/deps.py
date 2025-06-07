from typing import Annotated

import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Cookie, status, HTTPException
from fastapi.security import OAuth2PasswordBearer

from app.core.database import get_db_session
from app.services.token import is_token_blacklisted
from app.services.user import get_user_by_id
from app.models.user import User
from app.core.config import settings
from app.core.security import decode_token, verify_token_type
from app.core.exceptions import InvalidTokenException


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_BASE_PATH}/auth/login")
TokenDep = Annotated[str, Depends(oauth2_scheme)]

async def verify_access_token(token: TokenDep) -> dict:
    try:
        payload = decode_token(token)
        if payload is None:
            raise InvalidTokenException(detail="Token has expired or is invalid")
        verify_token_type(payload, "access")
        return payload
    except jwt.exceptions.PyJWTError as e:
        raise InvalidTokenException(detail=f"Invalid token: {str(e)}")


AsyncSessionDep = Annotated[AsyncSession, Depends(get_db_session)]

async def verify_refresh_token(
    session: AsyncSessionDep,
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


TokenPayloadDep = Annotated[dict, Depends(verify_access_token)]

async def get_current_user(
    session: AsyncSessionDep,
    token_payload: TokenPayloadDep
) -> User:
    """Get the current authenticated user"""
    user_id = token_payload.get("sub")
    if not user_id:
        raise InvalidTokenException()
    
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise InvalidTokenException()
    
    user = await get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


RefreshTokenPayloadDep = Annotated[dict, Depends(verify_refresh_token)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
