from typing import List
from pydantic import BaseModel


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
    timestamp: int  # Unix timestamp in milliseconds
    value: float
    
    
class MarketChartData(BaseModel):
    prices: List[ChartDataPoint]
    market_caps: List[ChartDataPoint] 
    volumes: List[ChartDataPoint] 