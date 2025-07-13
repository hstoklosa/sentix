import logging
from typing import List, Tuple, Optional
from datetime import datetime, time

from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, and_
from sqlalchemy.orm import selectinload

from app.models.news import Coin, NewsItem, NewsCoin
from app.core.news.types import NewsData
from app.core.market.coingecko import coingecko_client

logger = logging.getLogger(__name__)


async def get_coin_by_symbol(session: AsyncSession, symbol: str) -> Optional[Coin]:
    """Get a coin by its symbol"""
    stmt = select(Coin).where(Coin.symbol == symbol)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_news_item(session: AsyncSession, news_data: NewsData, sentiment: dict) -> NewsItem:
    """
    Create a news item (article or social post)
    
    Args:
        session: The database session
        news_data: The news data from TreeNews
        sentiment: The sentiment analysis result
    
    Returns:
        The created news item
    """
    item_type = 'post' if news_data.source == "Twitter" else 'article'
    item = NewsItem(
        title=news_data.title,
        body=news_data.body or "",
        image_url=news_data.image,
        time=news_data.time,
        source=news_data.source,
        url=news_data.url,
        icon_url=news_data.icon,
        feed=news_data.feed,
        item_type=item_type,
        sentiment=sentiment["label"],
        score=sentiment["score"]
    )
    
    print("debug3") 

    session.add(item)
    await session.commit()
    await session.refresh(item)

    print("debug4") 

    if news_data.coins:
        current_time = datetime.utcnow()
        coins_list = list(news_data.coins)

        coins_data = await coingecko_client.get_coins_markets(
            symbols=coins_list, include_tokens="top"
        )

        print("debug5") 

        for coin_data in coins_data:
            symbol = coin_data.get("symbol").upper()
            coin = await get_coin_by_symbol(session, symbol)
            
            # Skip coins that aren't found in database or CoinGecko
            if not coin:
                coin = Coin(
                    symbol=symbol,
                    name=coin_data.get("name"),
                    image_url=coin_data.get("image")
                )
                session.add(coin)
                await session.flush()
                
            news_coin = NewsCoin(
                coin_id=coin.id,
                news_item_id=item.id, 
                price_usd=coin_data.get("current_price"),
                price_timestamp=current_time
            )
            
            session.add(news_coin)

        print("debug6") 
        
        await session.commit()
        await session.refresh(item)

    print("debug7") 

    # Refresh with joined coin data
    # stmt = (
    #     select(NewsItem)
    #     .where(NewsItem.id == item.id)
    #     .options(selectinload(NewsItem.coins).selectinload(NewsCoin.coin))
    # )
    # result = await session.execute(stmt)
    # return result.scalar_one()

    # print("debug8")
    
    return item


async def save_news_item(session: AsyncSession, news_data: NewsData, sentiment: dict) -> NewsItem:
    """
    Save a news item (article or social post) based on its source
    
    Args:
        session: The database session
        news_data: The news data from TreeNews
        sentiment: The sentiment analysis result
    
    Returns:
        The created news item with coin relationships loaded
    """
    try:
        # Check if the URL already exists to avoid duplicates
        print("debug0") 
        stmt = select(NewsItem).where(NewsItem.url == news_data.url)
        result = await session.execute(stmt)
        existing_item = result.unique().scalar_one_or_none() # result.scalar_one_or_none()

        print("debug1") 

        if existing_item:
            logger.info(f"News item already exists: {existing_item.id} - {existing_item.title}")
            
            # Refresh with joined coin data
            stmt = (
                select(NewsItem)
                .where(NewsItem.id == existing_item.id)
                .options(selectinload(NewsItem.coins).selectinload(NewsCoin.coin))
            )
            result = await session.execute(stmt)
            existing_item = result.unique().scalar_one() # result.scalar_one()
            print("debug2") 
            return existing_item

        item = await create_news_item(session, news_data, sentiment)
        return item
        
    except Exception as e:
        logger.error(f"Error saving news item: {str(e)}")
        raise


async def get_news_feed(
    session: AsyncSession, 
    page: int = 1, 
    page_size: int = 20,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    start_time: Optional[time] = None,
    end_time: Optional[time] = None
) -> Tuple[List[NewsItem], int]:
    """
    Get a paginated feed of news items ordered by published date
    
    Args:
        session: The database session
        page: The page number (1-indexed)
        page_size: Number of items per page
        start_date: Optional start date for filtering (inclusive)
        end_date: Optional end date for filtering (inclusive)
        start_time: Optional start time for filtering (inclusive)
        end_time: Optional end time for filtering (inclusive)
    
    Returns:
        Tuple containing:
            - List of news items
            - Total count of items
    """
    print(f"DEBUG: get_news_feed called with start_date={start_date}, end_date={end_date}, start_time={start_time}, end_time={end_time}")
    
    offset = (page - 1) * page_size
    
    # Build date and time filter conditions
    date_conditions = []
    if start_date:
        date_conditions.append(NewsItem.time >= start_date)
    if end_date:
        date_conditions.append(NewsItem.time <= end_date)
    
    # Add time conditions if specified
    if start_time:
        date_conditions.append(func.extract('hour', NewsItem.time) * 60 + func.extract('minute', NewsItem.time) >= start_time.hour * 60 + start_time.minute)
    if end_time:
        date_conditions.append(func.extract('hour', NewsItem.time) * 60 + func.extract('minute', NewsItem.time) <= end_time.hour * 60 + end_time.minute)
    
    # Combine date conditions
    where_clause = and_(*date_conditions) if date_conditions else None
    
    # Get total count
    count_stmt = select(func.count()).select_from(NewsItem)
    if where_clause is not None:
        count_stmt = count_stmt.where(where_clause)
    result = await session.execute(count_stmt)
    total_count = result.scalar_one()
    
    # Query for items, sorted by time and paginated
    stmt = (
        select(NewsItem)
        .options(selectinload(NewsItem.coins).selectinload(NewsCoin.coin))
        .order_by(NewsItem.time.desc())
        .offset(offset)
        .limit(page_size)
    )
    if where_clause is not None:
        stmt = stmt.where(where_clause)
    
    result = await session.execute(stmt)
    items = result.unique().scalars().all()
    
    return items, total_count


async def search_news(
    session: AsyncSession,
    query: str,
    page: int = 1,
    page_size: int = 20,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Tuple[List[NewsItem], int]:
    """
    Search news items by query string in title and body
    
    Args:
        session: The database session
        query: The search query string
        page: The page number (1-indexed)
        page_size: Number of items per page
        start_date: Optional start date for filtering (inclusive)
        end_date: Optional end date for filtering (inclusive)
    
    Returns:
        Tuple containing:
            - List of news items matching the search query
            - Total count of matching items
    """
    offset = (page - 1) * page_size
    
    # Prepare search condition (title or body contains the query)
    search_term = f"%{query}%"
    search_condition = or_(
        NewsItem.title.ilike(search_term),
        NewsItem.body.ilike(search_term)
    )
    
    # Build date filter conditions
    date_conditions = []
    if start_date:
        date_conditions.append(NewsItem.time >= start_date)
    if end_date:
        date_conditions.append(NewsItem.time <= end_date)
    
    # Combine all conditions
    all_conditions = [search_condition]
    if date_conditions:
        all_conditions.extend(date_conditions)
    where_clause = and_(*all_conditions)
    
    # Count total matching items
    count_stmt = select(func.count()).select_from(NewsItem).where(where_clause)
    result = await session.execute(count_stmt)
    total_count = result.scalar_one()
    
    # Query for matching items, sorted by time and paginated
    stmt = (
        select(NewsItem)
        .where(where_clause)
        .options(selectinload(NewsItem.coins).selectinload(NewsCoin.coin))
        .order_by(NewsItem.time.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    items = result.unique().scalars().all()
    
    return items, total_count


async def get_post_by_id(session: AsyncSession, post_id: int) -> Optional[NewsItem]:
    """
    Args:
        session: The database session
        post_id: The post item ID
    
    Returns:
        The news item if found, None otherwise
    """
    stmt = (
        select(NewsItem)
        .where(NewsItem.id == post_id)
        .options(selectinload(NewsItem.coins).selectinload(NewsCoin.coin))
    )
    
    result = await session.execute(stmt)
    return result.unique().scalar_one_or_none() # result.scalar_one_or_none()
