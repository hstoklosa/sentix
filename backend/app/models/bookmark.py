from datetime import datetime

from sqlmodel import Field, Relationship
from sqlalchemy import UniqueConstraint

from app.models.base import Base
from app.models.news import NewsItem
from app.models.user import User


class NewsBookmark(Base, table=True):
    """Table to store user bookmarks for news items"""
    __tablename__ = "news_bookmarks"
    
    user_id: int = Field(foreign_key="users.id", index=True)
    news_item_id: int = Field(foreign_key="news_items.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Add a unique constraint to enforce one bookmark per user-news item pair
    __table_args__ = (
        UniqueConstraint("user_id", "news_item_id", name="unique_user_news_bookmark"),
    )
    
    # Relationships
    user: User = Relationship(back_populates="news_bookmarks")
    news_item: NewsItem = Relationship(back_populates="bookmarks") 