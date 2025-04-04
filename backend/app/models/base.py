from typing import Optional, Dict, Any, Type, TypeVar, cast
from datetime import datetime

from sqlalchemy import func
from sqlmodel import SQLModel, Field, Column, DateTime

T = TypeVar('T', bound=SQLModel)

def timestamp_field(nullable=False, **kwargs: Dict[str, Any]):
    """Factory function that returns a new timestamp field with timezone each time it's called"""
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

    # REF: https://github.com/fastapi/sqlmodel/issues/252
    # created_at: Optional[datetime] = Field(
    #     default=None,
    #     sa_column=Column(DateTime(timezone=True), server_default=func.now())
    # )
    # updated_at: Optional[datetime] = Field(
    #     default=None,
    #     sa_column=Column(
    #         DateTime(timezone=True),
    #         server_default=func.now(),
    #         onupdate=func.now(),
    #     )
    # )

    created_at: datetime = timestamp_field()
    updated_at: datetime = timestamp_field(onupdate=func.now())
