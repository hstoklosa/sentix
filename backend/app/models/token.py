from datetime import datetime
from sqlalchemy import func
from sqlmodel import SQLModel, Field, Column, DateTime, Boolean, String

from app.models.base import Base

class Token(SQLModel, table=True):
    """Model for tracking blacklisted refresh tokens"""
    __tablename__ = "tokens"
    
    id: int = Field(default=None, primary_key=True)
    jti: str = Field(..., nullable=False)
    expires_at: datetime = Field(..., nullable=False)
    is_blacklisted: bool = Field(default=True, nullable=False)

    # Instead of trying to override created_at, use it as blacklisted_at
    # created_at from Base will be used to track when the token was blacklisted
    created_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False
        )
    )
    updated_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False
        )
    )

    @property
    def blacklisted_at(self) -> datetime:
        """Return created_at as blacklisted_at"""
        return self.created_at 