from typing import Optional
from datetime import datetime

from sqlalchemy import func
from sqlmodel import SQLModel, Field, Column, DateTime

class Base(SQLModel):
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

    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False
        )
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False
        )
    )
