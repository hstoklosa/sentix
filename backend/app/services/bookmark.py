import logging

from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.bookmark import NewsBookmark
from app.models.news import NewsItem

logger = logging.getLogger(__name__)


async def create_bookmark(session: Session, user_id: int, news_item_id: int) -> NewsBookmark:
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
    news_item = session.exec(select(NewsItem).where(NewsItem.id == news_item_id)).first()
    if not news_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News item not found"
        )
    
    try:
        # Create bookmark
        bookmark = NewsBookmark(user_id=user_id, news_item_id=news_item_id)
        session.add(bookmark)
        session.commit()
        session.refresh(bookmark)
        return bookmark
    except IntegrityError:
        session.rollback()
        # Get existing bookmark if it was a duplicate
        existing = session.exec(
            select(NewsBookmark)
            .where(NewsBookmark.user_id == user_id, NewsBookmark.news_item_id == news_item_id)
        ).first()
        if existing:
            return existing
        
        logger.error(f"Error creating bookmark for user {user_id}, news {news_item_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to create bookmark"
        )


async def delete_bookmark(session: Session, user_id: int, news_item_id: int) -> bool:
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
    bookmark = session.exec(stmt).first()
    
    if bookmark:
        session.delete(bookmark)
        session.commit()
        return True
    
    return False
