from typing import List, Tuple, Dict, Any, Optional

import logging

from sqlmodel import Session, select, func
from sqlalchemy.orm import joinedload, selectinload

from app.models.news import Coin, NewsItem, NewsCoin
from app.core.news.types import NewsData

logger = logging.getLogger(__name__)


async def get_or_create_coin(session: Session, symbol: str) -> Coin:
    """
    Get a coin by symbol or create it if it doesn't exist
    
    Args:
        session: The database session
        symbol: The coin symbol
    
    Returns:
        The coin object
    """
    stmt = select(Coin).where(Coin.symbol == symbol)
    coin = session.exec(stmt).first()
    
    if not coin:
        coin = Coin(symbol=symbol)
        session.add(coin)
        session.commit()
        session.refresh(coin)
    
    return coin


async def create_news_item(session: Session, news_data: NewsData, sentiment: dict) -> NewsItem:
    """
    Create a news item (article or social post)
    
    Args:
        session: The database session
        news_data: The news data from TreeNews
    
    Returns:
        The created news item
    """
    # Determine item type based on source
    item_type = 'post' if news_data.source == "Twitter" else 'article'
    
    # Create the news item
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
    
    # Add coins to the news item
    if news_data.coins:
        for symbol in news_data.coins:
            coin = await get_or_create_coin(session, symbol)
            news_coin = NewsCoin(news_item_id=item.id, coin_id=coin.id)
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
