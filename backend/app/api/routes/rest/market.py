from fastapi import APIRouter

from app.core.market.coinmarketcap import cmc_client
from app.schemas.market import MarketStats

router = APIRouter(
    prefix="/market",
    tags=["market"]
)


@router.get("/", response_model=MarketStats)
async def get_market_stats():
    stats = cmc_client.get_market_stats()
    fear_greed_index = cmc_client.get_fear_greed_index()
    quote_usd = stats.get("data", {}).get("quote", {}).get("USD", {})
    
    return MarketStats(
        total_market_cap=quote_usd.get("total_market_cap", 0.0),
        total_market_cap_24h_change=quote_usd.get("total_market_cap_yesterday_percentage_change", 0.0),
        total_volume_24h=quote_usd.get("total_volume_24h", 0.0),
        total_volume_24h_change=quote_usd.get("total_volume_24h_yesterday_percentage_change", 0.0),
        btc_dominance=stats.get("data", {}).get("btc_dominance", 0.0),
        eth_dominance=stats.get("data", {}).get("eth_dominance", 0.0),
        btc_dominance_24h_change=stats.get("data", {}).get("btc_dominance_24h_percentage_change", 0.0),
        eth_dominance_24h_change=stats.get("data", {}).get("eth_dominance_24h_percentage_change", 0.0),
        fear_and_greed_index=fear_greed_index.get("data", {}).get("value", 50)
    )
