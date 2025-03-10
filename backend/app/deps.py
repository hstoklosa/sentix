from typing import Annotated

from sqlmodel import Session
from fastapi import Depends, Cookie
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.core.db import get_session
from app.core.config import settings
from app.core.security import decode_token, verify_token_type, get_token_jti
from app.core.exceptions import InvalidTokenException
from app.services.token import is_token_blacklisted

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_BASE_PATH}/auth/login"
)

async def verify_access_token(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[Session, Depends(get_session)]
) -> dict:
    try:
        payload = decode_token(token)
        verify_token_type(payload, "access")
        return payload
    except JWTError:
        raise InvalidTokenException()


async def verify_refresh_token(
    session: Annotated[Session, Depends(get_session)],
    refresh_token: str | None = Cookie(None, include_in_schema=False)
) -> dict:
    """Verify that the refresh token is valid and not blacklisted"""
    if not refresh_token:
        raise InvalidTokenException()
    
    try:
        payload = decode_token(refresh_token)
        verify_token_type(payload, "refresh")
        
        # Check if token is blacklisted
        jti = get_token_jti(payload)
        if jti and is_token_blacklisted(session=session, jti=jti):
            raise InvalidTokenException()
            
        return payload
    except JWTError:
        raise InvalidTokenException()
    
SessionDep = Annotated[Session, Depends(get_session)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]
TokenPayloadDep = Annotated[dict, Depends(verify_access_token)]
RefreshTokenPayloadDep = Annotated[dict, Depends(verify_refresh_token)]
