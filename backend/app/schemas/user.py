from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator

from app.core.security import validate_password

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(..., max_length=255)
    is_superuser: bool = Field(default=False)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=64)
    
    @validator('password')
    def validate_password_field(cls, v):
        is_valid, error_message = validate_password(v)
        if not is_valid:
            raise ValueError(error_message)
        return v

class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str = Field(..., min_length=8, max_length=64)
    
    @validator('password')
    def validate_password_field(cls, v):
        is_valid, error_message = validate_password(v)
        if not is_valid:
            raise ValueError(error_message)
        return v
    
    @validator('username')
    def validate_login_fields(cls, v, values):
        email = values.get('email')
        if not email and not v:
            raise ValueError('Either email or username must be provided')
        return v

class UserPublic(UserBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
