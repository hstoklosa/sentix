from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func
from datetime import datetime, time, date
from typing import Annotated

from app.core.market.coinmarketcap import cmc_client
from app.core.market.coingecko import coingecko_client
from app.schemas.market import MarketStats, CoinResponse, PaginationParams, PaginatedResponse
from app.models.news import NewsItem
from app.core.db import get_session

router = APIRouter(
    prefix="/market",
    tags=["market"]
)


@router.get("/", response_model=MarketStats)
async def get_market_stats(session: Session = Depends(get_session)):
    stats = cmc_client.get_market_stats()
    fear_greed_index = cmc_client.get_fear_greed_index()
    quote_usd = stats.get("data", {}).get("quote", {}).get("USD", {})
    
    # Get today's date and calculate start/end timestamps
    today = date.today()
    start_of_day = datetime.combine(today, time.min)
    end_of_day = datetime.combine(today, time.max)
    
    # Query for today's news items
    today_news = session.exec(
        select(NewsItem)
        .where(NewsItem.time >= start_of_day)
        .where(NewsItem.time <= end_of_day)
    ).all()
    
    # Count sentiment types
    bullish_count = sum(1 for item in today_news if item.sentiment == "Bullish")
    bearish_count = sum(1 for item in today_news if item.sentiment == "Bearish")
    neutral_count = sum(1 for item in today_news if item.sentiment == "Neutral")
    
    # Calculate overall sentiment
    market_sentiment = "Neutral"
    total_posts = len(today_news)
    
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
    pagination: Annotated[PaginationParams, Depends()],
    session: Session = Depends(get_session)
):
    # Get coins with pagination parameters
    coins = coingecko_client.get_coins_markets(
        page=pagination.page,
        limit=pagination.page_size
    )
    
    # Total count is not directly available from the API
    # We'll have to estimate based on the assumption that the total is at least 
    # the number of items returned, and likely more
    items_count = len(coins)
    total_items = max(items_count, 5000)  # Assuming CoinGecko has ~5000 coins
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
