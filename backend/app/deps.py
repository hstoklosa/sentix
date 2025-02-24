from typing import Annotated

from sqlmodel import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.core.db import get_session
from app.core.config import settings
from app.core.security import decode_token, verify_token_type
from app.core.exceptions import InvalidTokenException

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_BASE_PATH}/auth/login"
)


async def verify_access_token(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    try:
        payload = decode_token(token)
        verify_token_type(payload, "access")
        return payload
    except JWTError:
        raise InvalidTokenException()
    
SessionDep = Annotated[Session, Depends(get_session)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]
TokenPayloadDep = Annotated[dict, Depends(verify_access_token)]
