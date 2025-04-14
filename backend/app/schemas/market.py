from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List


class MarketStats(BaseModel):
    total_market_cap: float
    total_market_cap_24h_change: float
    total_volume_24h: float
    total_volume_24h_change: float
    btc_dominance: float
    eth_dominance: float
    btc_dominance_24h_change: float
    eth_dominance_24h_change: float
    fear_and_greed_index: int
    market_sentiment: str = "Neutral"


class PaginationParams(BaseModel):
    """Pagination parameters for API requests"""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of items per page")


T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool
    items: List[T]


class CoinResponse(BaseModel):
    id: str
    symbol: str
    name: str
    image: str
    current_price: float
    market_cap: float
    market_cap_rank: int
    price_change_percentage_24h: float | None = None
    volume_24h: float
    