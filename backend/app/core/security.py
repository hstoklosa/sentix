from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any

from passlib.context import CryptContext
from jose import JWTError, jwt

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(
        subject: Union[str, Any], 
        expires_delta: Optional[timedelta] = None,
        extra_claims: Optional[dict[str, Any]] = None
):
    if expires_delta:
        expiration = datetime.now(timezone.utc) + expires_delta
    else:
        expiration = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = { **extra_claims, "sub": str(subject), "exp": expiration }
    encoded = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        raise e

def verify_token_type(token_data: dict, token_type: str):
    if token_data.get("type") != token_type:
        raise JWTError("Invalid token type")