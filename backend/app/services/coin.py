import logging
from datetime import datetime, time, date, timedelta
from typing import List, Tuple, Dict, Any, Union, Literal

from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
import ccxt.async_support as ccxt_async

from app.core.database import sessionmanager
from app.providers.market.coingecko import CoinGeckoClient, coingecko_client
from app.models.coin import Coin
from app.models.post import Post
from app.models.post_coin import PostCoin

logger = logging.getLogger(__name__)


async def get_trending_coins_by_mentions(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Get trending coins based on mentions in posts for the current day,
    ordered by number of mentions and with sentiment statistics.
    """
    today = date.today()
    start_of_day = datetime.combine(today, time.min)
    end_of_day = datetime.combine(today, time.max)
    
    # Get coins mentioned in today's posts with the mention count
    subquery = (
        select(PostCoin.coin_id, func.count(Post.id).label("mention_count"))
        .join(Post, Post.id == PostCoin.post_id)
        .where(Post.time >= start_of_day)
        .where(Post.time <= end_of_day)
        .group_by(PostCoin.coin_id)
        .subquery()
    )
    
    # Get total count for pagination
    count_query = select(func.count()).select_from(subquery)
    result = await session.execute(count_query)
    total_count = result.scalar_one()
    
    # Get coin details with mention count, ordered by mention count
    offset = (page - 1) * page_size
    
    query = (
        select(Coin, subquery.c.mention_count)
        .join(subquery, Coin.id == subquery.c.coin_id)
        .order_by(subquery.c.mention_count.desc())
        .offset(offset)
        .limit(page_size)
    )
    
    result = await session.execute(query)
    results = result.all()

    # Process the results with sentiment statistics
    trending_coins = []
    for coin, mention_count in results:
        # Get all posts mentioning this coin today
        posts_query = (
            select(Post)
            .options(joinedload(Post.post_coins))  # Use post_coins instead of coins
            .join(PostCoin, Post.id == PostCoin.post_id)
            .where(PostCoin.coin_id == coin.id)
            .where(Post.time >= start_of_day)
            .where(Post.time <= end_of_day)
        )
        result = await session.execute(posts_query)
        posts = result.unique().scalars().all()

        # Calculate sentiment statistics
        positive_count = sum(1 for post in posts if post.sentiment == "Bullish")
        negative_count = sum(1 for post in posts if post.sentiment == "Bearish")
        neutral_count = sum(1 for post in posts if post.sentiment == "Neutral")
        
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


async def sync_coins_from_coingecko():
    """Sync coins from CoinGecko API to database (async version)"""
    client = CoinGeckoClient()
    coins_list = await client.get_coins_markets()
    
    if not coins_list:
        logger.error("Failed to fetch coins list from CoinGecko API")
        return
    
    logger.info(f"Fetched {len(coins_list)} coins from CoinGecko")
    
    async with sessionmanager.session() as session:
        for coin_data in coins_list:
            try:
                coin_id = coin_data.get("id")
                symbol = coin_data.get("symbol", "").upper()
                name = coin_data.get("name", "")
                image_url = coin_data.get("image", "")
                
                if not coin_id or not symbol or not name or not image_url:
                    continue
                
                # Check if coin already exists
                stmt = select(Coin).where(Coin.symbol == symbol)
                result = await session.execute(stmt)
                existing_coin = result.scalar_one_or_none()
                
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
        
        await session.commit()
    
    logger.info("Coin synchronisation completed")


async def get_coin_sentiment_divergence_history(
    session: AsyncSession,
    coin_id: str,
    days: Union[int, Literal["max"]] = 30,
    interval: str = "daily"
) -> List[Dict[str, Any]]:
    """
    Get historical sentiment divergence data for a coin, including:
    - Average sentiment score
    - Social volume (mentions)
    - Price data from CCXT (primary) or post_coins (fallback)
    - Divergence signals
    """
    # Calculate date range
    end_date = datetime.utcnow()
    if days == "max":
        start_date = datetime.min
    else:
        start_date = end_date - timedelta(days=days)
    
    # First get the coin by symbol
    coin_query = select(Coin).where(Coin.symbol == coin_id.upper())
    result = await session.execute(coin_query)
    coin = result.scalar_one_or_none()
    
    if not coin:
        return []
    
    # Query posts mentioning the coin within date range
    posts_query = (
        select(Post)
        .join(PostCoin)
        .where(PostCoin.coin_id == coin.id)
        .where(Post.time >= start_date)
        .where(Post.time <= end_date)
        .order_by(Post.time.asc())
    )
    
    result = await session.execute(posts_query)
    posts = result.unique().scalars().all()
    
    # Group by interval (day/hour) and calculate metrics
    grouped_data = {}
    for post in posts:
        if interval == "daily":
            timestamp = post.time.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            timestamp = post.time.replace(minute=0, second=0, microsecond=0)
            
        if timestamp not in grouped_data:
            grouped_data[timestamp] = {
                "mentions": 0,
                "sentiment_sum": 0,
                "price": None,
                "price_timestamp": None
            }
            
        group = grouped_data[timestamp]
        group["mentions"] += 1
        
        # Convert sentiment label to score: Bullish=1, Neutral=0, Bearish=-1
        sentiment_score = {
            "Bullish": 1,
            "Neutral": 0,
            "Bearish": -1
        }.get(post.sentiment, 0)
        group["sentiment_sum"] += sentiment_score
        
        # Get price data from post_coins (as fallback)
        for post_coin in post.post_coins:
            if post_coin.coin_id == coin.id and post_coin.price_usd is not None:
                group["price"] = post_coin.price_usd
                group["price_timestamp"] = post_coin.price_timestamp

    # Fetch historical price data from CCXT
    ccxt_interval = "1d" if interval == "daily" else "1h"
    pair = f"{coin_id.upper()}/USDT"
    price_data = {}
    
    try:
        binance = ccxt_async.binance()
        await binance.load_markets()
        
        if binance.markets is not None and pair in binance.markets:
            since = None if days == "max" else int(start_date.timestamp() * 1000)
            limit = None if days == "max" else (days if ccxt_interval == "1d" else days * 24)
            
            ohlcv = await binance.fetch_ohlcv(
                pair, timeframe=ccxt_interval, since=since, limit=limit
            )
            
            # Create a mapping of timestamps to prices
            for timestamp_ms, _, _, _, close_price, _ in ohlcv:
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                if interval == "daily":
                    timestamp = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
                else:
                    timestamp = timestamp.replace(minute=0, second=0, microsecond=0)
                price_data[timestamp] = close_price
                
                # Initialize sentiment data for timestamps with price but no posts
                if timestamp not in grouped_data:
                    grouped_data[timestamp] = {
                        "mentions": 0,
                        "sentiment_sum": 0,
                        "price": None,
                        "price_timestamp": None
                    }
    except Exception as e:
        logger.error(f"Error fetching CCXT price data: {str(e)}")
    finally:
        if 'binance' in locals():
            await binance.close()
    
    # Calculate averages and format response
    sentiment_data = []
    prev_sentiment = None
    prev_mentions = None
    prev_price = None
    
    for timestamp, data in sorted(grouped_data.items()):
        mentions = data["mentions"]
        avg_sentiment = data["sentiment_sum"] / mentions if mentions > 0 else 0
        
        # Use CCXT price if available, otherwise fallback to post_coin price
        price = price_data.get(timestamp) or data["price"]
        
        # Calculate divergence signals
        divergence = None
        if prev_sentiment is not None and prev_mentions is not None and prev_price is not None:
            # Bullish divergence: Price ↓, but sentiment ↑
            if price and price < prev_price and avg_sentiment > prev_sentiment:
                divergence = "bullish"
            # Bearish divergence: Social volume ↑, but sentiment ↓ or flat
            elif mentions > prev_mentions * 1.5 and avg_sentiment <= prev_sentiment:
                divergence = "bearish"
        
        point = {
            "timestamp": timestamp.isoformat(),
            "average_sentiment": avg_sentiment,
            "mentions": mentions,
            "price": price,
            "divergence": divergence
        }
        sentiment_data.append(point)
        
        # Update previous values
        prev_sentiment = avg_sentiment
        prev_mentions = mentions
        prev_price = price
    
    return sentiment_data
