from typing import List, TYPE_CHECKING

from pydantic import EmailStr
from sqlmodel import Field, Relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.bookmark import PostBookmark


class User(Base, table=True):
    __tablename__ = "users"

    username: str = Field(unique=True, index=True, max_length=50)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_superuser: bool = Field(default=False)
    password: str
    
    # Relationships
    post_bookmarks: List["PostBookmark"] = Relationship(back_populates="user")
