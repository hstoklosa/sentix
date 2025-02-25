from typing import Optional
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from jose import jwt, JWTError

from app.core.config import settings
from app.core.exceptions import InvalidCredentialsException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


"""
PASSWORDS
"""
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

"""
AUTH TOKENS (JWT)
"""
def create_token(
        data: dict, 
        expires_delta: Optional[timedelta] = None, 
        token_type: str = "access"
) -> str:
    raw_data = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    elif token_type == "access":
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:  # token_type == "refresh"
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    
    raw_data.update({"exp": expire, "type": token_type})
    
    return jwt.encode(raw_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    return create_token(data, expires_delta, token_type="access")

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    return create_token(data, expires_delta, token_type="refresh")

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise InvalidCredentialsException()

def verify_token_type(token_data: dict, token_type: str):
    if token_data.get("type") != token_type:
        raise JWTError("Invalid token type")
