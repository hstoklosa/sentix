from pydantic import BaseModel


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
