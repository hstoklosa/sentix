from typing import List
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.news import NewsItem, PaginatedResponse


class BookmarkCreate(BaseModel):
    news_item_id: int


class BookmarkResponse(BaseModel):
    id: int
    user_id: int
    news_item_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class BookmarkedNewsItem(NewsItem):
    bookmark_id: int
    bookmarked_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class BookmarkedNewsResponse(PaginatedResponse):
    items: List[BookmarkedNewsItem] 