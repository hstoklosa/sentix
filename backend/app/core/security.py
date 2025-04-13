from typing import Optional
from datetime import datetime, timedelta, timezone
import uuid
import re

from passlib.context import CryptContext
from jose import jwt, JWTError

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate that a password meets the security requirements specified by regex.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Check if password is at least 8 characters
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    # Check if password contains at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    # Check if password contains at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    # Check if password contains at least one digit
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    # Check if password contains at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character!!"
    
    return True, None


def get_password_hash(password: str) -> str:
    """Hash the provided password after validation is handled by the schema."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(
    subject: str | int, 
    token_type: str = "access"
) -> str:
    if token_type == "access":
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    
    raw_data = {
        "type": token_type,
        "jti": str(uuid.uuid4()), # add id for blacklisting
        "sub": str(subject),
        "iat": datetime.now(timezone.utc),
        "exp": expire
    }
    
    return jwt.encode(raw_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str | int) -> str:
    return create_token(subject, token_type="access")


def create_refresh_token(subject: str | int) -> str:
    return create_token(subject, token_type="refresh")


def decode_token(token: str) -> Optional[dict]:
    """
    Decode JWT token and return the payload, or None if token is invalid.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None 


def verify_token_type(token_data: dict, expected_type: str) -> bool:
    """
    Verify token type, return True if valid, False otherwise.
    """
    return token_data.get("type") == expected_type


def get_token_jti(token_data: dict) -> Optional[str]:
    """Extract JTI from token data"""
    return token_data.get("jti")
