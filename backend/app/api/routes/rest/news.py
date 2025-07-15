import math

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import AsyncSessionDep, CurrentUserDep
from app.services.news import get_news_feed, get_post_by_id, search_news
from app.schemas.news import (
    NewsItem as NewsItemSchema,
    NewsFeedResponse, 
    SearchParams,
    DateFilterParams
)
from app.services.bookmark import is_bookmarked
from app.schemas.pagination import PaginationParams
from app.models.user import User
from app.utils import format_datetime_iso

router = APIRouter(
    prefix="/news",
    tags=["news"]
)


@router.get("/", response_model=NewsFeedResponse)
async def get_posts(
    session: AsyncSessionDep,
    pagination: PaginationParams = Depends(),
    date_filter: DateFilterParams = Depends(),
    current_user: User = CurrentUserDep
) -> NewsFeedResponse:
    """Get a paginated list of posts ordered by published date"""
    items, total_count = await get_news_feed(
        session=session, 
        page=pagination.page,
        page_size=pagination.page_size,
        start_date=date_filter.start_date,
        end_date=date_filter.end_date
    )
    
    # Calculate pagination metadata
    total_pages = math.ceil(total_count / pagination.page_size) if total_count > 0 else 0
    has_next = pagination.page < total_pages
    has_prev = pagination.page > 1
    
    # Transform SQLModel instances to schema objects with properly formatted data
    news_items = []
    for item in items:
        item_dict = item.model_dump()
        item_dict["coins"] = item.get_formatted_coins()
        item_dict["is_bookmarked"] = await is_bookmarked(
            session=session,
            user_id=current_user.id,
            news_item_id=item.id
        )
        item_dict["time"] = format_datetime_iso(item.time)
        item_dict["created_at"] = format_datetime_iso(item.created_at)
        item_dict["updated_at"] = format_datetime_iso(item.updated_at)
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


@router.get("/search", response_model=NewsFeedResponse)
async def search_posts(
    session: AsyncSessionDep,
    current_user: CurrentUserDep,
    search: SearchParams = Depends(),
    pagination: PaginationParams = Depends(),
    date_filter: DateFilterParams = Depends(),
) -> NewsFeedResponse:
    """Search news items by query string"""
    items, total_count = await search_news(
        session=session,
        query=search.query,
        page=pagination.page,
        page_size=pagination.page_size,
        start_date=date_filter.start_date,
        end_date=date_filter.end_date
    )
    
    # Calculate pagination metadata
    total_pages = math.ceil(total_count / pagination.page_size) if total_count > 0 else 0
    has_next = pagination.page < total_pages
    has_prev = pagination.page > 1
    
    # Transform SQLModel instances to schema objects with properly formatted data
    news_items = []
    for item in items:
        item_dict = item.model_dump()
        item_dict["coins"] = item.get_formatted_coins()
        item_dict["is_bookmarked"] = await is_bookmarked(
            session=session,
            user_id=current_user.id,
            news_item_id=item.id
        )
        item_dict["time"] = format_datetime_iso(item.time)
        item_dict["created_at"] = format_datetime_iso(item.created_at)
        item_dict["updated_at"] = format_datetime_iso(item.updated_at)
        
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
    session: AsyncSessionDep,
    current_user: CurrentUserDep
) -> NewsItemSchema:
    """Get a post by its ID"""
    post = await get_post_by_id(session=session, post_id=post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Transform SQLModel instances to schema objects with properly formatted data
    post_dict = post.model_dump()
    post_dict["time"] = format_datetime_iso(post.time)
    post_dict["created_at"] = format_datetime_iso(post.created_at)
    post_dict["updated_at"] = format_datetime_iso(post.updated_at)
    post_dict["coins"] = post.get_formatted_coins()
    post_dict["is_bookmarked"] = await is_bookmarked(
        session=session, user_id=current_user.id, news_item_id=post.id)
    
    return NewsItemSchema.model_validate(post_dict)
