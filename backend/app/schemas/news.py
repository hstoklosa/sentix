from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.pagination import PaginatedResponse


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
