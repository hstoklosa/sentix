from typing import Optional
from datetime import datetime, timedelta, timezone
import uuid
import re

from passlib.context import CryptContext
from jose import jwt, JWTError

from app.core.config import settings
from app.core.exceptions import InvalidCredentialsException, InvalidPasswordException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


"""
PASSWORDS
"""
def validate_password(password: str) -> bool:
    """
    Validate that a password meets the security requirements:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character
    
    Returns True if valid, raises InvalidPasswordException otherwise.
    """
    # Check if password is at least 8 characters
    if len(password) < 8:
        raise InvalidPasswordException("Password must be at least 8 characters long")
    
    # Check if password contains at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        raise InvalidPasswordException("Password must contain at least one uppercase letter")
    
    # Check if password contains at least one lowercase letter
    if not re.search(r'[a-z]', password):
        raise InvalidPasswordException("Password must contain at least one lowercase letter")
    
    # Check if password contains at least one digit
    if not re.search(r'\d', password):
        raise InvalidPasswordException("Password must contain at least one number")
    
    # Check if password contains at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise InvalidPasswordException("Password must contain at least one special character")
    
    return True

def get_password_hash(password: str) -> str:
    # Password validation is handled by the schemas before this function is called
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
    
    # Add JWT ID for token identification (useful for blacklisting)
    jti = str(uuid.uuid4())
    
    raw_data.update({
        "exp": expire, 
        "type": token_type,
        "jti": jti,
        "iat": datetime.now(timezone.utc)
    })
    
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

def get_token_jti(token_data: dict) -> Optional[str]:
    """Extract JTI from token data"""
    return token_data.get("jti")
