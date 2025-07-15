from datetime import datetime, time, date
from typing import Annotated, Union, Literal, List, Dict, Any
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

import ccxt.async_support as ccxt_async

from app.core.market.coinmarketcap import cmc_client
from app.core.market.coingecko import coingecko_client
from app.schemas.market import MarketStats, CoinResponse, MarketChartData, ChartDataPoint
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.models.post import Post
from app.deps import AsyncSessionDep
from app.services.coin import (
    get_trending_coins_by_mentions,
    sync_coins_from_coingecko,
    get_coin_sentiment_divergence_history
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/market",
    tags=["market"]
)


@router.get("/", response_model=MarketStats)
async def get_market_stats(
    session: AsyncSessionDep,
    force_refresh: bool = False
):
    # Use force_refresh parameter to bypass cache if requested
    stats = await cmc_client.get_market_stats(force_refresh=force_refresh)
    fear_greed_index = await cmc_client.get_fear_greed_index(force_refresh=force_refresh)
    
    quote_usd = stats.get("data", {}).get("quote", {}).get("USD", {})
    
    # Get today's date and calculate start/end timestamps
    today = date.today()
    start_of_day = datetime.combine(today, time.min)
    end_of_day = datetime.combine(today, time.max)
    
    # Query for today's posts
    stmt = (
        select(Post)
        .where(Post.time >= start_of_day)
        .where(Post.time <= end_of_day)
    )
    result = await session.execute(stmt)
    today_posts = result.scalars().unique().all()
    
    # Count sentiment types
    bullish_count = sum(1 for post in today_posts if post.sentiment == "Bullish")
    bearish_count = sum(1 for post in today_posts if post.sentiment == "Bearish")
    neutral_count = sum(1 for post in today_posts if post.sentiment == "Neutral")
    
    # Calculate overall sentiment
    market_sentiment = "Neutral"
    total_posts = len(today_posts)
    
    if total_posts > 0:
        # Calculate ratio of bullish to bearish
        sentiment_ratio = (bullish_count - bearish_count) / total_posts
        
        # Determine overall sentiment
        if sentiment_ratio > 0.1:  # More than 10% positive bias
            market_sentiment = "Bullish"
        elif sentiment_ratio < -0.1:  # More than 10% negative bias
            market_sentiment = "Bearish"
    
    return MarketStats(
        total_market_cap=quote_usd.get("total_market_cap", 0.0),
        total_market_cap_24h_change=quote_usd.get("total_market_cap_yesterday_percentage_change", 0.0),
        total_volume_24h=quote_usd.get("total_volume_24h", 0.0),
        total_volume_24h_change=quote_usd.get("total_volume_24h_yesterday_percentage_change", 0.0),
        btc_dominance=stats.get("data", {}).get("btc_dominance", 0.0),
        eth_dominance=stats.get("data", {}).get("eth_dominance", 0.0),
        btc_dominance_24h_change=stats.get("data", {}).get("btc_dominance_24h_percentage_change", 0.0),
        eth_dominance_24h_change=stats.get("data", {}).get("eth_dominance_24h_percentage_change", 0.0),
        fear_and_greed_index=fear_greed_index.get("data", {}).get("value", 50),
        market_sentiment=market_sentiment
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
    # Validate interval parameter
    if interval not in VALID_CHART_INTERVALS:
        interval = "daily"
    ccxt_interval = VALID_CHART_INTERVALS[interval]

    # Validate days parameter
    if days not in VALID_CHART_DAYS and days != "max":
        days = 30

    # coin_id is the symbol of the coin
    pair = f"{coin_id.upper()}/USDT"

    # Fetch OHLCV data from Binance using ccxt
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
