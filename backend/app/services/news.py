import logging
from typing import List, Tuple, Optional
from datetime import datetime

from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, and_
from sqlalchemy.orm import selectinload

from app.models.coin import Coin
from app.models.post import Post
from app.models.post_coin import PostCoin
from app.core.news.types import NewsData
from app.providers.market.coingecko import coingecko_client

logger = logging.getLogger(__name__)


async def get_coin_by_symbol(session: AsyncSession, symbol: str) -> Optional[Coin]:
    """Get a coin by its symbol"""
    stmt = select(Coin).where(Coin.symbol == symbol)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_post(session: AsyncSession, post_data: NewsData, sentiment: dict) -> Post:
    """Create a post entry (article or social post) within the database"""
    item_type = 'post' if post_data.source == "Twitter" else 'article'
    item = Post(
        title=post_data.title,
        body=post_data.body or "",
        image_url=post_data.image,
        time=post_data.time,
        source=post_data.source,
        url=post_data.url,
        icon_url=post_data.icon,
        feed=post_data.feed,
        item_type=item_type,
        sentiment=sentiment["label"],
        score=sentiment["score"]
    )
    
    session.add(item)
    await session.commit()
    await session.refresh(item)

    if post_data.coins:
        current_time = datetime.utcnow()
        coins_list = list(post_data.coins)

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
                
            news_coin = PostCoin(
                coin_id=coin.id,
                post_id=item.id, 
                price_usd=coin_data.get("current_price"),
                price_timestamp=current_time
            )
            
            session.add(news_coin)
        
        await session.commit()
        await session.refresh(item)

    # Refresh with joined coin data to avoid lazy loading issues
    stmt = (
        select(Post)
        .where(Post.id == item.id)
        .options(selectinload(Post.post_coins).selectinload(PostCoin.coin))
    )
    result = await session.execute(stmt)
    item_with_coins = result.unique().scalar_one()
    
    return item_with_coins


async def save_news_item(session: AsyncSession, post_data: NewsData, sentiment: dict) -> Post:
    """Save a news item (article or social post) based on its source"""
    try:
        stmt = select(Post).where(Post.url == post_data.url)
        result = await session.execute(stmt)
        existing_post = result.unique().scalar_one_or_none()

        if existing_post:
            logger.info(f"Post already exists: {existing_post.id} - {existing_post.title}")
            
            # Refresh with joined coin data
            stmt = (
                select(Post)
                .where(Post.id == existing_post.id)
                .options(selectinload(Post.post_coins).selectinload(PostCoin.coin))
            )
            result = await session.execute(stmt)
            existing_post = result.unique().scalar_one()
            return existing_post

        post = await create_post(session, post_data, sentiment)
        return post
        
    except Exception as e:
        logger.error(f"Error saving post: {str(e)}")
        raise


async def get_news_feed(
    session: AsyncSession, 
    page: int = 1, 
    page_size: int = 20,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    coin_symbol: Optional[str] = None
) -> Tuple[List[Post], int]:
    """Get a paginated feed of news posts ordered by published date"""
    offset = (page - 1) * page_size
    
    # Build date and time filter conditions
    date_conditions = []
    if start_date:
        date_conditions.append(Post.time >= start_date)
    if end_date:
        date_conditions.append(Post.time <= end_date)
    
    # Note: If time filtering is needed separately from date,
    # it should be combined with date filtering in the frontend
    # before sending to the backend for better performance
    
    # Add coin filter condition if specified
    if coin_symbol:
        coin_filter_condition = (
            Post.id.in_(
                select(PostCoin.post_id)
                .join(Coin)
                .where(Coin.symbol == coin_symbol.upper())
            )
        )
        date_conditions.append(coin_filter_condition)
    
    # Combine date conditions
    where_clause = and_(*date_conditions) if date_conditions else None
    count_stmt = select(func.count()).select_from(Post)

    if where_clause is not None:
        count_stmt = count_stmt.where(where_clause)

    result = await session.execute(count_stmt)
    total_count = result.scalar_one()
    
    # Load posts with their relationships
    stmt = (
        select(Post)
        .options(selectinload(Post.post_coins).selectinload(PostCoin.coin))
        .order_by(Post.time.desc())
        .offset(offset)
        .limit(page_size)
    )
    if where_clause is not None:
        stmt = stmt.where(where_clause)
    
    result = await session.execute(stmt)
    posts = result.unique().scalars().all()
    
    return posts, total_count


async def search_news(
    session: AsyncSession,
    query: str,
    page: int = 1,
    page_size: int = 20,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    coin_symbol: Optional[str] = None
) -> Tuple[List[Post], int]:
    """Search posts by query string in title and body"""
    offset = (page - 1) * page_size
    
    search_term = f"%{query}%"
    search_condition = or_(
        Post.title.ilike(search_term),
        Post.body.ilike(search_term)
    )
    
    date_conditions = []
    if start_date:
        date_conditions.append(Post.time >= start_date)
    if end_date:
        date_conditions.append(Post.time <= end_date)
    
    # Note: If time filtering is needed separately from date,
    # it should be combined with date filtering in the frontend
    # before sending to the backend for better performance
    
    # Add coin filter condition if specified
    if coin_symbol:
        coin_filter_condition = (
            Post.id.in_(
                select(PostCoin.post_id)
                .join(Coin)
                .where(Coin.symbol == coin_symbol.upper())
            )
        )
        date_conditions.append(coin_filter_condition)
    
    all_conditions = [search_condition]
    if date_conditions:
        all_conditions.extend(date_conditions)
    where_clause = and_(*all_conditions)
    
    count_stmt = select(func.count()).select_from(Post).where(where_clause)
    result = await session.execute(count_stmt)
    total_count = result.scalar_one()
    
    # Query for matching items, sorted by time and paginated
    stmt = (
        select(Post)
        .where(where_clause)
        .options(selectinload(Post.post_coins).selectinload(PostCoin.coin))
        .order_by(Post.time.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    posts = result.unique().scalars().all()
    
    return posts, total_count


async def get_post_by_id(session: AsyncSession, post_id: int) -> Optional[Post]:
    stmt = (
        select(Post)
        .where(Post.id == post_id)
        .options(selectinload(Post.post_coins).selectinload(PostCoin.coin))
    )
    
    result = await session.execute(stmt)
    return result.unique().scalar_one_or_none()
