from datetime import datetime
from sqlalchemy import func
from sqlmodel import SQLModel, Field

from app.models.base import timestamp_field


class Token(SQLModel, table=True):
    """Model for tracking blacklisted refresh tokens"""
    __tablename__ = "tokens"
    
    id: int = Field(default=None, primary_key=True)
    jti: str = Field(..., nullable=False)
    expires_at: datetime = Field(..., nullable=False)
    is_blacklisted: bool = Field(default=True, nullable=False)

    created_at: datetime = timestamp_field()
    updated_at: datetime = timestamp_field(onupdate=func.now())

    @property
    def blacklisted_at(self) -> datetime:
        """Return created_at as blacklisted_at"""
        return self.created_at 