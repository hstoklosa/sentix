from typing import List, Optional

from pydantic import EmailStr
from sqlmodel import Field, Relationship

from app.models.base import Base

class User(Base, table=True):
    __tablename__ = "users"

    username: str = Field(unique=True, index=True, max_length=50)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_superuser: bool = Field(default=False)
    password: str
    
    # Add relationship to bookmarks (must be at the end to avoid circular imports)
    news_bookmarks: List["NewsBookmark"] = Relationship(back_populates="user")
