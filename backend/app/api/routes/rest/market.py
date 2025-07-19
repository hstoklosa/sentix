import logging
from typing import Annotated, Union, Literal, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException

import ccxt.async_support as ccxt_async

from app.providers.market.coingecko import coingecko_client
from app.schemas.market import CoinResponse, MarketChartData, ChartDataPoint
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.deps import AsyncSessionDep
from app.services.coin import get_coin_sentiment_divergence_history

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/market",
    tags=["market"]
)


@router.get("/coins", response_model=PaginatedResponse[CoinResponse])
async def get_coins(
    session: AsyncSessionDep,
    pagination: Annotated[PaginationParams, Depends()],
    force_refresh: bool = False,
):
    # Get coins with pagination parameters and optional force refresh
    coins = await coingecko_client.get_coins_markets(
        page=pagination.page,
        limit=pagination.page_size,
        force_refresh=force_refresh
    )
    
    # Total count is not provided by the API (i.e., using an estimation)
    items_count = len(coins)
    total_items = max(items_count, 5000)
    total_pages = (total_items + pagination.page_size - 1) // pagination.page_size
    
    # Map the response to CoinResponse objects
    coin_responses = [
        CoinResponse(
            id=coin.get("id", ""),
            symbol=coin.get("symbol", ""),
            name=coin.get("name", ""),
            image=coin.get("image", ""),
            current_price=coin.get("current_price", 0.0),
            market_cap=coin.get("market_cap", 0.0),
            market_cap_rank=coin.get("market_cap_rank", 0),
            price_change_percentage_24h=coin.get("price_change_percentage_24h"),
            volume_24h=coin.get("total_volume", 0.0)
        )
        for coin in coins
    ]
    
    return PaginatedResponse(
        page=pagination.page,
        page_size=pagination.page_size,
        total=total_items,
        total_pages=total_pages,
        has_next=pagination.page < total_pages,
        has_prev=pagination.page > 1,
        items=coin_responses
    )


VALID_CHART_INTERVALS = {"daily": "1d", "hourly": "1h"}
VALID_CHART_DAYS = [1, 7, 14, 30, 90, 180, 365, "max"]

@router.get("/coins/{coin_id}/chart", response_model=MarketChartData)
async def get_coin_chart_data(
    session: AsyncSessionDep,
    coin_id: str,
    days: Union[int, Literal["max"]] = 30,
    interval: str = "daily",
):
    if interval not in VALID_CHART_INTERVALS:
        interval = "daily"
    ccxt_interval = VALID_CHART_INTERVALS[interval]

    if days not in VALID_CHART_DAYS and days != "max":
        days = 30

    # coin_id is the symbol of the coin
    pair = f"{coin_id.upper()}/USDT"

    binance = ccxt_async.binance()
    
    try:
        # Load markets to ensure the pair exists
        await binance.load_markets()
        
        if binance.markets is None or pair not in binance.markets:
            raise HTTPException(status_code=404, detail=f"Pair {pair} not found on Binance")

        # since = binance.milliseconds() - days * 24 * 60 * 60 * 1000
        # limit = days if ccxt_interval == "1d" else days * 24

        since = None if days == "max" else binance.milliseconds() - days * 24 * 60 * 60 * 1000
        limit = None if days == "max" else (days if ccxt_interval == "1d" else days * 24)
        
        ohlcv = await binance.fetch_ohlcv(
            pair, timeframe=ccxt_interval, since=since, limit=limit)

    except Exception as e:
        logger.error(f"Error occurred while fetching chart data from CCXT: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch chart data: {e}")
    finally:
        await binance.close()

    # Transform OHLCV to ChartDataPoint (timestamp, close price)
    prices = [
        ChartDataPoint(
            timestamp=timestamp, 
            value=close_price
        ) for timestamp, _, _, _, close_price, _ in ohlcv
    ]
    volumes = [
        ChartDataPoint(
            timestamp=timestamp, 
            value=volume
        ) for timestamp, _, _, _, _, volume in ohlcv
    ]
    market_caps = [] # ccxt does not provide market cap data 

    return MarketChartData(
        prices=prices,
        market_caps=market_caps,
        volumes=volumes
    )


@router.get("/coins/{coin_id}/sentiment-divergence", response_model=List[Dict[str, Any]])
async def get_coin_sentiment_divergence(
    session: AsyncSessionDep,
    coin_id: str,
    days: Union[int, Literal["max"]] = 30,
    interval: str = "daily"
):
    """Get historical sentiment divergence data for a specific coin"""
    if interval not in ["daily", "hourly"]:
        interval = "daily"
    if days not in [1, 7, 14, 30, 90, 180, 365] and days != "max":
        days = 30
        
    divergence_data = await get_coin_sentiment_divergence_history(
        session=session,
        coin_id=coin_id,
        days=days,
        interval=interval
    )
    return divergence_data
