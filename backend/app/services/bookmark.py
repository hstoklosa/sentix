import logging
from typing import List, Tuple, Optional
from datetime import datetime

from fastapi import HTTPException, status
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy import or_, and_

from app.models.bookmark import PostBookmark
from app.models.post import Post

logger = logging.getLogger(__name__)


async def create_bookmark(session: AsyncSession, user_id: int, post_id: int) -> PostBookmark:
    result = await session.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    try:
        bookmark = PostBookmark(user_id=user_id, post_id=post_id)
        session.add(bookmark)
        await session.commit()
        await session.refresh(bookmark)
        return bookmark
    except IntegrityError:
        await session.rollback()
        # Get existing bookmark if it was a duplicate
        result = await session.execute(
            select(PostBookmark)
            .where(PostBookmark.user_id == user_id, PostBookmark.post_id == post_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        
        logger.error(f"Error creating bookmark for user {user_id}, post {post_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to create bookmark"
        )


async def delete_bookmark(session: AsyncSession, user_id: int, post_id: int) -> bool:
    stmt = (
        select(PostBookmark)
        .where(
            PostBookmark.user_id == user_id,
            PostBookmark.post_id == post_id
        )
    )
    result = await session.execute(stmt)
    
    if bookmark := result.scalar_one_or_none():
        await session.delete(bookmark)
        await session.commit()
        return True
    
    return False


async def is_bookmarked(session: AsyncSession, user_id: int, post_id: int) -> bool:
    stmt = (
        select(PostBookmark)
        .where(
            PostBookmark.user_id == user_id,
            PostBookmark.post_id == post_id
        )
    )
    result = await session.execute(stmt)
    bookmark = result.scalar_one_or_none()
    return bookmark is not None


async def get_user_bookmarks(
    session: AsyncSession, 
    user_id: int, 
    page: int = 1, 
    page_size: int = 20,
    search_query: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    coin_symbol: Optional[str] = None
) -> Tuple[List[dict], int]:
    offset = (page - 1) * page_size
    
    # Build filter conditions
    filter_conditions = [PostBookmark.user_id == user_id]
    
    # Add search condition if provided
    if search_query:
        search_term = f"%{search_query}%"
        search_condition = or_(
            Post.title.ilike(search_term),
            Post.body.ilike(search_term)
        )
        filter_conditions.append(search_condition)
    
    # Add date filter conditions
    if start_date:
        filter_conditions.append(Post.time >= start_date)
    if end_date:
        filter_conditions.append(Post.time <= end_date)
    
    # Add coin filter condition
    if coin_symbol:
        from app.models.post_coin import PostCoin
        from app.models.coin import Coin
        filter_conditions.append(
            Post.id.in_(
                select(PostCoin.post_id)
                .join(Coin, PostCoin.coin_id == Coin.id)
                .where(Coin.symbol == coin_symbol)
            )
        )
    else:
        # Import PostCoin for selectinload even when not filtering by coin
        from app.models.post_coin import PostCoin
    
    # Combine all filter conditions
    where_clause = and_(*filter_conditions)
    
    # Count total matching items
    count_stmt = (
        select(func.count())
        .select_from(PostBookmark)
        .join(Post, PostBookmark.post_id == Post.id)
        .where(where_clause)
    )
    result = await session.execute(count_stmt)
    total_count = result.scalar_one()
    
    # Get bookmarked items with post data
    stmt = (
        select(Post, PostBookmark)
        .join(PostBookmark, Post.id == PostBookmark.post_id)
        .where(where_clause)
        .options(selectinload(Post.post_coins).selectinload(PostCoin.coin))
        .order_by(PostBookmark.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    
    result = await session.execute(stmt)
    results = result.all()
    
    # Combine posts with bookmark information
    items = []
    for post, bookmark in results:
        # Convert to dict and add bookmark info
        item_dict = {
            **post.model_dump(),  # Changed from dict() to model_dump() for Pydantic v2
            "bookmark_id": bookmark.id,
            "bookmarked_at": bookmark.created_at
        }
        items.append(item_dict)
    
    return items, total_count 