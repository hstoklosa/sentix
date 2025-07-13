from datetime import datetime, time
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.pagination import PaginatedResponse


class DateFilterParams(BaseModel):
    """Parameters for filtering news by date and time range"""
    start_date: Optional[datetime] = Field(None, description="Start date for filtering (inclusive)")
    end_date: Optional[datetime] = Field(None, description="End date for filtering (inclusive)")
    start_time: Optional[time] = Field(None, description="Start time for filtering (inclusive)")
    end_time: Optional[time] = Field(None, description="End time for filtering (inclusive)")


class SearchParams(BaseModel):
    query: str = Field(..., min_length=1, description="Search query string")


class CoinResponse(BaseModel):
    id: int
    symbol: str
    name: Optional[str] = None
    image_url: Optional[str] = None
    price_usd: Optional[float] = None
    price_timestamp: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class NewsItem(BaseModel):
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

    model_config = ConfigDict(from_attributes=True)


class NewsFeedResponse(PaginatedResponse):
    items: List[NewsItem]
