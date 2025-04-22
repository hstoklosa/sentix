import logging
import asyncio
from datetime import datetime, time, date
from typing import List, Tuple, Dict, Any

from sqlmodel import select, Session, func

from app.core.db import engine
from app.core.market.coingecko import CoinGeckoClient
from app.models.coin import Coin
from app.models.news import NewsItem, NewsCoin

logger = logging.getLogger(__name__)


async def get_trending_coins_by_mentions(
    session: Session,
    page: int = 1,
    page_size: int = 20
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Get trending coins based on mentions in posts for the current day,
    ordered by number of mentions and with sentiment statistics.
    
    Args:
        session: The database session
        page: The page number (1-indexed)
        page_size: Number of items per page
    
    Returns:
        Tuple containing:
            - List of trending coins with mention count and sentiment stats
            - Total count of coins mentioned today
    """
    # Get today's date and calculate start/end timestamps
    today = date.today()
    start_of_day = datetime.combine(today, time.min)
    end_of_day = datetime.combine(today, time.max)
    
    # Query to get coins mentioned in today's posts with mention count
    subquery = (
        select(
            NewsCoin.coin_id,
            func.count(NewsItem.id).label("mention_count")
        )
        .join(NewsItem, NewsItem.id == NewsCoin.news_item_id)
        .where(NewsItem.time >= start_of_day)
        .where(NewsItem.time <= end_of_day)
        .group_by(NewsCoin.coin_id)
        .subquery()
    )
    
    # Get total count for pagination
    count_query = select(func.count()).select_from(subquery)
    total_count = session.exec(count_query).one()
    
    # Get coin details with mention count, ordered by mention count
    offset = (page - 1) * page_size
    
    query = (
        select(
            Coin,
            subquery.c.mention_count
        )
        .join(subquery, Coin.id == subquery.c.coin_id)
        .order_by(subquery.c.mention_count.desc())
        .offset(offset)
        .limit(page_size)
    )
    
    results = session.exec(query).all()

    # Process the results with sentiment statistics
    trending_coins = []
    for coin, mention_count in results:
        # Get all news items mentioning this coin today
        news_query = (
            select(NewsItem)
            .join(NewsCoin, NewsItem.id == NewsCoin.news_item_id)
            .where(NewsCoin.coin_id == coin.id)
            .where(NewsItem.time >= start_of_day)
            .where(NewsItem.time <= end_of_day)
        )
        news_items = session.exec(news_query).all()
        
        # Calculate sentiment statistics
        positive_count = sum(1 for item in news_items if item.sentiment == "Bullish")
        negative_count = sum(1 for item in news_items if item.sentiment == "Bearish")
        neutral_count = sum(1 for item in news_items if item.sentiment == "Neutral")
        
        # Create the trending coin object
        trending_coin = {
            "id": coin.id,
            "symbol": coin.symbol,
            "name": coin.name,
            "image_url": coin.image_url,
            "mention_count": mention_count,
            "sentiment_stats": {
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count
            }
        }
        trending_coins.append(trending_coin)
    
    return trending_coins, total_count


async def async_sync_coins_from_coingecko():
    """Sync coins from CoinGecko API to database (async version)"""
    client = CoinGeckoClient()
    coins_list = await client.get_coins_markets()
    
    if not coins_list:
        logger.error("Failed to fetch coins list from CoinGecko API")
        return
    
    logger.info(f"Fetched {len(coins_list)} coins from CoinGecko")
    
    with Session(engine) as session:
        for coin_data in coins_list:
            try:
                coin_id = coin_data.get("id")
                symbol = coin_data.get("symbol", "").upper()
                name = coin_data.get("name", "")
                image_url = coin_data.get("image", "")
                
                if not coin_id or not symbol or not name or not image_url:
                    continue
                
                # Check if coin already exists
                statement = select(Coin).where(Coin.symbol == symbol)
                existing_coin = session.exec(statement).first()
                
                # Update existing coin or create new one
                if existing_coin:
                    existing_coin.name = name
                    existing_coin.image_url = image_url
                    session.add(existing_coin)
                else:
                    new_coin = Coin(
                        symbol=symbol,
                        name=name,
                        image_url=image_url
                    )
                    session.add(new_coin)
            except Exception as e:
                logger.error(f"Error processing coin {coin_data.get('symbol')}: {str(e)}")
                continue
        
        session.commit()
    
    logger.info("Coin synchronisation completed")


def sync_coins_from_coingecko():
    """
    Sync coins from CoinGecko API to database (synchronous wrapper)
    This function creates an event loop and runs the async function
    """
    # Run the async function in the event loop
    asyncio.run(async_sync_coins_from_coingecko()) 