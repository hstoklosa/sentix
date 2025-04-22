from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List

from app.schemas.pagination import PaginatedResponse

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
    

class ChartDataPoint(BaseModel):
    """Data point for price charts"""
    timestamp: int  # Unix timestamp in milliseconds
    value: float
    
    
class MarketChartData(BaseModel):
    """Historical market data for charts"""
    prices: List[ChartDataPoint]
    market_caps: List[ChartDataPoint] 
    volumes: List[ChartDataPoint] 