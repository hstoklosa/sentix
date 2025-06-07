from typing import List, Tuple
import logging

from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.bookmark import NewsBookmark
from app.models.news import NewsItem

logger = logging.getLogger(__name__)


async def create_bookmark(session: AsyncSession, user_id: int, news_item_id: int) -> NewsBookmark:
    """
    Create a bookmark for a news item
    
    Args:
        session: The database session
        user_id: User ID who is creating the bookmark
        news_item_id: ID of the news item to bookmark
    
    Returns:
        The created bookmark
        
    Raises:
        HTTPException: If news item doesn't exist or bookmark already exists
    """
    # Check if news item exists
    result = await session.execute(select(NewsItem).where(NewsItem.id == news_item_id))
    news_item = result.scalar_one_or_none()
    if not news_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News item not found"
        )
    
    try:
        # Create bookmark
        bookmark = NewsBookmark(user_id=user_id, news_item_id=news_item_id)
        session.add(bookmark)
        await session.commit()
        await session.refresh(bookmark)
        return bookmark
    except IntegrityError:
        await session.rollback()
        # Get existing bookmark if it was a duplicate
        result = await session.execute(
            select(NewsBookmark)
            .where(NewsBookmark.user_id == user_id, NewsBookmark.news_item_id == news_item_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        
        logger.error(f"Error creating bookmark for user {user_id}, news {news_item_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to create bookmark"
        )


async def delete_bookmark(session: AsyncSession, user_id: int, news_item_id: int) -> bool:
    """
    Delete a user's bookmark for a news item
    
    Args:
        session: The database session
        user_id: User ID who owns the bookmark
        news_item_id: ID of the bookmarked news item
    
    Returns:
        True if deleted, False if not found
    """
    stmt = (
        select(NewsBookmark)
        .where(
            NewsBookmark.user_id == user_id,
            NewsBookmark.news_item_id == news_item_id
        )
    )
    result = await session.execute(stmt)
    bookmark = result.scalar_one_or_none()
    
    if bookmark:
        await session.delete(bookmark)
        await session.commit()
        return True
    
    return False


async def is_bookmarked(session: AsyncSession, user_id: int, news_item_id: int) -> bool:
    """
    Check if a news item is bookmarked by a user
    
    Args:
        session: The database session
        user_id: User ID to check
        news_item_id: News item ID to check
    
    Returns:
        True if bookmarked, False otherwise
    """
    stmt = (
        select(NewsBookmark)
        .where(
            NewsBookmark.user_id == user_id,
            NewsBookmark.news_item_id == news_item_id
        )
    )
    result = await session.execute(stmt)
    bookmark = result.scalar_one_or_none()
    return bookmark is not None


async def get_user_bookmarks(
    session: AsyncSession, 
    user_id: int, 
    page: int = 1, 
    page_size: int = 20
) -> Tuple[List[dict], int]:
    """
    Get a paginated list of a user's bookmarked news items
    
    Args:
        session: The database session
        user_id: User ID to get bookmarks for
        page: The page number (1-indexed)
        page_size: Number of items per page
    
    Returns:
        Tuple containing:
            - List of news items with bookmark information
            - Total count of bookmarked items
    """
    offset = (page - 1) * page_size
    
    # Get total count
    count_stmt = (
        select(func.count())
        .select_from(NewsBookmark)
        .where(NewsBookmark.user_id == user_id)
    )
    result = await session.execute(count_stmt)
    total_count = result.scalar_one()
    
    # Get bookmarked items with news item data
    stmt = (
        select(NewsItem, NewsBookmark)
        .join(NewsBookmark, NewsItem.id == NewsBookmark.news_item_id)
        .where(NewsBookmark.user_id == user_id)
        .options(selectinload(NewsItem.coins))
        .order_by(NewsBookmark.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    
    result = await session.execute(stmt)
    results = result.all()
    
    # Combine news items with bookmark information
    items = []
    for news_item, bookmark in results:
        # Convert to dict and add bookmark info
        item_dict = {
            **news_item.model_dump(),  # Changed from dict() to model_dump() for Pydantic v2
            "bookmark_id": bookmark.id,
            "bookmarked_at": bookmark.created_at
        }
        items.append(item_dict)
    
    return items, total_count 