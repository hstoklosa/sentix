from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.pagination import PaginatedResponse


class CoinBase(BaseModel):
    id: int
    symbol: str
    name: Optional[str] = None
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CoinWithPrice(CoinBase):
    price_usd: Optional[float] = None
    price_timestamp: Optional[datetime] = None


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

    model_config = ConfigDict(from_attributes=True)


class TrendingCoinsResponse(PaginatedResponse):
    items: List[TrendingCoin] 