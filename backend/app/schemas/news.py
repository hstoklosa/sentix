from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.pagination import PaginatedResponse


class SearchParams(BaseModel):
    """Search parameters for news item queries"""
    query: str = Field(..., min_length=1, description="Search query string")


# class PaginatedResponse(BaseModel):
#     """Generic paginated response"""
#     page: int
#     page_size: int
#     total: int
#     total_pages: int
#     has_next: bool
#     has_prev: bool


class CoinResponse(BaseModel):
    """Coin response model"""
    id: int
    symbol: str
    name: Optional[str] = None
    image_url: Optional[str] = None
    price_usd: Optional[float] = None
    price_timestamp: Optional[datetime] = None
    
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
    sentiment: str
    score: float

    class Config:
        from_attributes = True

class NewsFeedResponse(PaginatedResponse):
    """Paginated response containing news feed items"""
    items: List[NewsItem]
