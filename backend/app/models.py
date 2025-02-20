from datetime import datetime
from typing import Optional

from sqlalchemy import func
from pydantic import EmailStr

from sqlmodel import SQLModel, Field, Column, DateTime

# BASE MODEL
class Base(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)

    # REF: https://github.com/fastapi/sqlmodel/issues/252
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
        )
    )

# USER MODELS
class UserBase(Base):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_superuser: bool = False

class User(UserBase, table=True):
    password: str

class UserPublic(UserBase):
    pass

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=64)
