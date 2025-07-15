from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.coin import CoinBase
from app.schemas.pagination import PaginatedResponse


class DateFilterParams(BaseModel):
    """Parameters for filtering news by date and time range"""
    start_date: Optional[datetime] = Field(None, description="Start date for filtering (inclusive)")
    end_date: Optional[datetime] = Field(None, description="End date for filtering (inclusive)")


class CoinFilterParams(BaseModel):
    """Parameters for filtering news by cryptocurrency"""
    coin: Optional[str] = Field(None, description="Cryptocurrency symbol to filter by (e.g., BTC, ETH)")


class SearchParams(BaseModel):
    query: str = Field(..., min_length=1, description="Search query string")


class CoinInPost(BaseModel):
    """Represents a coin within a post with price information"""
    coin_id: int
    price_usd: Optional[float] = None
    price_timestamp: Optional[datetime] = None
    coin: "CoinBase"
    
    model_config = ConfigDict(from_attributes=True)


class CoinResponse(BaseModel):
    id: int
    symbol: str
    name: Optional[str] = None
    image_url: Optional[str] = None
    price_usd: Optional[float] = None
    price_timestamp: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_post_coin(cls, post_coin) -> "CoinResponse":
        """Create CoinResponse from PostCoin relationship"""
        return cls(
            id=post_coin.coin.id,
            symbol=post_coin.coin.symbol,
            name=post_coin.coin.name,
            image_url=post_coin.coin.image_url,
            price_usd=post_coin.price_usd,
            price_timestamp=post_coin.price_timestamp
        )


class Post(BaseModel):
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
    coins: List[CoinResponse] = Field(default_factory=list)
    is_bookmarked: bool = False
    sentiment: str
    score: float

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class NewsFeedResponse(PaginatedResponse):
    items: List[Post]
