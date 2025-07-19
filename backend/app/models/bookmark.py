from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship
from sqlalchemy import UniqueConstraint, Index

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.post import Post
    from app.models.user import User


class PostBookmark(Base, table=True):
    __tablename__ = "post_bookmarks"
    
    user_id: int = Field(foreign_key="users.id", index=True)
    post_id: int = Field(foreign_key="posts.id", index=True)
    # created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # __table_args__ = (
    #     UniqueConstraint("user_id", "post_id", name="unique_user_post_bookmark"),
    # )

    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="unique_user_post_bookmark"),
        Index("ix_bookmarks_user_created", "user_id", "created_at"),
        Index("ix_bookmarks_user_post", "user_id", "post_id"),
    )
    
    # user: "User" = Relationship(back_populates="post_bookmarks")
    # post: "Post" = Relationship(back_populates="post_bookmarks") 

    user: "User" = Relationship(back_populates="post_bookmarks")
    post: "Post" = Relationship()  # No back_populates to avoid circular loading