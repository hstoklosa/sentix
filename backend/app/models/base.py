from typing import Optional, Dict, Any, TypeVar
from datetime import datetime

from sqlalchemy import func
from sqlmodel import SQLModel, Field, DateTime


T = TypeVar('T', bound=SQLModel)

def timestamp_field(nullable=False, **kwargs: Dict[str, Any]):
    """Factory function that returns a new timestamp field with timezone"""
    return Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),
            "nullable": nullable,
            **kwargs
        }
    )

class Base(SQLModel):
    """Base model with common fields"""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = timestamp_field()
    updated_at: datetime = timestamp_field(onupdate=func.now())
