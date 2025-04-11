from datetime import datetime
from typing import List

from pydantic import BaseModel

from app.schemas.news import NewsItem, PaginatedResponse


class BookmarkCreate(BaseModel):
    """Schema for creating a news bookmark"""
    news_item_id: int


class BookmarkResponse(BaseModel):
    """Response schema for a bookmark operation"""
    user_id: int
    news_item_id: int
    created_at: datetime
    id: int
    
    class Config:
        from_attributes = True


class BookmarkedNewsItem(NewsItem):
    """News item with bookmark information"""
    bookmark_id: int
    bookmarked_at: datetime
    
    class Config:
        from_attributes = True


class BookmarkedNewsResponse(PaginatedResponse):
    """Paginated response containing bookmarked news items"""
    items: List[BookmarkedNewsItem] 