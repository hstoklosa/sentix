from typing import List, Optional
from pydantic import BaseModel

from app.schemas.pagination import PaginatedResponse


class SentimentStats(BaseModel):
    positive: int
    negative: int
    neutral: int


class TrendingCoin(BaseModel):
    id: int
    symbol: str
    name: Optional[str] = None
    image_url: Optional[str] = None
    mention_count: int
    sentiment_stats: SentimentStats

    class Config:
        from_attributes = True


class TrendingCoinsResponse(PaginatedResponse):
    items: List[TrendingCoin] 