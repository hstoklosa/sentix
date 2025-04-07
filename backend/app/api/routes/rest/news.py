import math

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.deps import get_session
from app.services.news import get_news_feed, get_post_by_id
from app.schemas.news import (
    PaginationParams, 
    NewsFeedResponse, 
    NewsItem as NewsItemSchema
)

router = APIRouter(
    prefix="/news",
    tags=["news"]
)


@router.get("/feed", response_model=NewsFeedResponse)
async def get_news_feed_endpoint(
    pagination: PaginationParams = Depends(),
    session: Session = Depends(get_session)
) -> NewsFeedResponse:
    """
    Get a paginated feed of posts (articles and social) ordered by published date
    
    Args:
        pagination: Pagination parameters
        session: Database session
    
    Returns:
        Paginated response containing news feed items
    """
    items, total_count = await get_news_feed(
        session=session, 
        page=pagination.page,
        page_size=pagination.page_size
    )
    
    # Calculate pagination metadata
    total_pages = math.ceil(total_count / pagination.page_size) if total_count > 0 else 0
    has_next = pagination.page < total_pages
    has_prev = pagination.page > 1
    
    # Properly transform the SQLModel instances to dict 
    # with properly structured relationships
    news_items = []
    for item in items:
        item_dict = item.model_dump()
        coin_list = []

        for news_coin in item.coins:
            if not news_coin.coin:
                continue

            coin_list.append({
                "id": news_coin.coin.id,
                "symbol": news_coin.coin.symbol,
                "name": news_coin.coin.name
            })
        
        # Replace the coins relationship with the transformed list
        item_dict["coins"] = coin_list
        news_items.append(NewsItemSchema.model_validate(item_dict))

    return NewsFeedResponse(
        page=pagination.page,
        page_size=pagination.page_size,
        total=total_count,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev,
        items=news_items
    )


@router.get("/{post_id}", response_model=NewsItemSchema)
async def get_post(
    post_id: int,
    session: Session = Depends(get_session)
) -> NewsItemSchema:
    """
    Get a post by its ID
    
    Args:
        post_id: The news item ID
        session: Database session
    
    Returns:
        The news item
    """
    post = await get_post_by_id(session=session, post_id=post_id)
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Transform the SQLModel instance to dict with properly structured relationships
    post_dict = post.model_dump()
    coin_list = []
    
    for news_coin in post.coins:
        if not news_coin.coin:
            continue
            
        coin_list.append({
            "id": news_coin.coin.id,
            "symbol": news_coin.coin.symbol,
            "name": news_coin.coin.name
        })
    
    # Replace the coins relationship with the transformed list
    post_dict["coins"] = coin_list
    return NewsItemSchema.model_validate(post_dict)
