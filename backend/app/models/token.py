from datetime import datetime
from typing import Optional
from sqlmodel import Field, Column, DateTime, func

from app.models.base import Base

class Token(Base, table=True):
    """Model for tracking blacklisted refresh tokens"""
    __tablename__ = "tokens"
    
    jti: str = Field(index=True, unique=True)
    expires_at: datetime
    is_blacklisted: bool = Field(default=True)
    
    # Override created_at from Base to use as blacklisted_at
    blacklisted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    ) 