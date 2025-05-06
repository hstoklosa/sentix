import logging
from typing import List, Tuple, Optional
from datetime import datetime

from sqlmodel import Session, select, func, or_
from sqlalchemy.orm import selectinload

from app.models.news import Coin, NewsItem, NewsCoin
from app.core.news.types import NewsData
from app.core.market.coingecko import coingecko_client

logger = logging.getLogger(__name__)


async def get_coin_by_symbol(session: Session, symbol: str) -> Optional[Coin]:
    """Get a coin by symbol"""
    return session.exec(select(Coin).where(Coin.symbol == symbol)).first()


async def create_news_item(session: Session, news_data: NewsData, sentiment: dict) -> NewsItem:
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
    
    session.add(item)
    session.commit()
    session.refresh(item)
    
    if news_data.coins:
        current_time = datetime.utcnow()
        coins_list = list(news_data.coins)

        coins_data = await coingecko_client.get_coins_markets(
            symbols=coins_list, include_tokens="top"
        )

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
    
        session.commit()

    # Refresh with joined coin data
    stmt = (
        select(NewsItem)
        .where(NewsItem.id == item.id)
        .options(selectinload(NewsItem.coins).selectinload(NewsCoin.coin))
    )
    item = session.exec(stmt).one()
    return item


async def save_news_item(session: Session, news_data: NewsData, sentiment: dict) -> NewsItem:
    """
    Save a news item (article or social post) based on its source
    
    Args:
        session: The database session
        news_data: The news data from TreeNews
    
    Returns:
        The created news item with coin relationships loaded
    """
    try:
        # Check if the URL already exists to avoid duplicates
        stmt = select(NewsItem).where(NewsItem.url == news_data.url)
        existing_item = session.exec(stmt).first()
        if existing_item:
            logger.info(f"News item already exists: {existing_item.id} - {existing_item.title}")
            
            # Refresh with joined coin data
            stmt = (
                select(NewsItem)
                .where(NewsItem.id == existing_item.id)
                .options(selectinload(NewsItem.coins).selectinload(NewsCoin.coin))
            )
            existing_item = session.exec(stmt).one()
            
            return existing_item
        
        return await create_news_item(session, news_data, sentiment)
    except Exception as e:
        logger.error(f"Error saving news item: {str(e)}")
        raise


async def get_news_feed(
    session: Session, 
    page: int = 1, 
    page_size: int = 20
) -> Tuple[List[NewsItem], int]:
    """
    Get a paginated feed of news items ordered by published date
    
    Args:
        session: The database session
        page: The page number (1-indexed)
        page_size: Number of items per page
    
    Returns:
        Tuple containing:
            - List of news items
            - Total count of items
    """
    offset = (page - 1) * page_size
    total_count = session.exec(select(func.count()).select_from(NewsItem)).one()
    
    # Query for items, sorted by time and paginated
    stmt = (
        select(NewsItem)
        .options(selectinload(NewsItem.coins).selectinload(NewsCoin.coin))
        .order_by(NewsItem.time.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = session.exec(stmt).all()
    
    return items, total_count


async def search_news(
    session: Session,
    query: str,
    page: int = 1,
    page_size: int = 20
) -> Tuple[List[NewsItem], int]:
    """
    Search news items by query string in title and body
    
    Args:
        session: The database session
        query: The search query string
        page: The page number (1-indexed)
        page_size: Number of items per page
    
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
    
    # Count total matching items
    count_stmt = select(func.count()).select_from(NewsItem).where(search_condition)
    total_count = session.exec(count_stmt).one()
    
    # Query for matching items, sorted by time and paginated
    stmt = (
        select(NewsItem)
        .where(search_condition)
        .options(selectinload(NewsItem.coins).selectinload(NewsCoin.coin))
        .order_by(NewsItem.time.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = session.exec(stmt).all()
    
    return items, total_count


async def get_post_by_id(session: Session, post_id: int) -> Optional[NewsItem]:
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
    
    item = session.exec(stmt).first()
    return item
