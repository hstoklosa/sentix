from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Pagination parameters for API requests"""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of items per page")


class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class CoinResponse(BaseModel):
    """Coin response model"""
    id: int
    symbol: str
    name: Optional[str] = None
    
    class Config:
        from_attributes = True


class NewsItem(BaseModel):
    """Base response model for news items"""
    id: int
    _type: str
    feed: str
    title: str
    body: Optional[str] = None
    image_url: Optional[str] = None
    time: datetime
    url: str
    source: str
    icon_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    coins: List[CoinResponse] = []
    is_bookmarked: bool = False

    class Config:
        from_attributes = True

class NewsFeedResponse(PaginatedResponse):
    """Paginated response containing news feed items"""
    items: List[NewsItem]
