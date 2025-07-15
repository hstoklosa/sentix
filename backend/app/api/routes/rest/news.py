import math

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.deps import AsyncSessionDep, CurrentUserDep
from app.services.news import get_news_feed, get_post_by_id, search_news
from app.schemas.news import (
    Post as PostSchema,
    NewsFeedResponse, 
    SearchParams,
    DateFilterParams,
    CoinFilterParams,
    CoinResponse
)
from app.services.bookmark import is_bookmarked
from app.schemas.pagination import PaginationParams
from app.utils import format_datetime_iso

router = APIRouter(
    prefix="/news",
    tags=["news"]
)


@router.get("/", response_model=NewsFeedResponse)
async def get_posts(
    session: AsyncSessionDep,
    current_user: CurrentUserDep,
    pagination: PaginationParams = Depends(),
    date_filter: DateFilterParams = Depends(),
    coin_filter: CoinFilterParams = Depends()
) -> NewsFeedResponse:
    """Get a paginated list of posts ordered by published date"""
    posts, total_count = await get_news_feed(
        session=session, 
        page=pagination.page,
        page_size=pagination.page_size,
        start_date=date_filter.start_date,
        end_date=date_filter.end_date,
        coin_symbol=coin_filter.coin
    )
    
    # Calculate pagination metadata
    total_pages = math.ceil(total_count / pagination.page_size) if total_count > 0 else 0
    has_next = pagination.page < total_pages
    has_prev = pagination.page > 1
    
    # Load ALL bookmarks for these posts in ONE query instead of N queries
    from app.models.bookmark import PostBookmark
    post_ids = [post.id for post in posts]
    bookmarks_stmt = select(PostBookmark.post_id).where(
        PostBookmark.user_id == current_user.id,
        PostBookmark.post_id.in_(post_ids)
    )
    result = await session.execute(bookmarks_stmt)
    bookmarked_post_ids = set(result.scalars().all())
    
    # Use Pydantic's from_attributes properly
    post_items = []
    for post in posts:
        # Use SQLModel's built-in Pydantic integration
        post_schema = PostSchema.model_validate(post, from_attributes=True)
        
        # Transform post_coins to coins using the proper method
        post_schema.coins = [
            CoinResponse.from_post_coin(post_coin) 
            for post_coin in post.post_coins
        ]
        
        # Override only the bookmark status
        post_schema.is_bookmarked = post.id in bookmarked_post_ids
        post_items.append(post_schema)

    return NewsFeedResponse(
        page=pagination.page,
        page_size=pagination.page_size,
        total=total_count,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev,
        items=post_items
    )


@router.get("/search", response_model=NewsFeedResponse)
async def search_posts(
    session: AsyncSessionDep,
    current_user: CurrentUserDep,
    search: SearchParams = Depends(),
    pagination: PaginationParams = Depends(),
    date_filter: DateFilterParams = Depends(),
    coin_filter: CoinFilterParams = Depends(),
) -> NewsFeedResponse:
    """Search news items by query string"""
    posts, total_count = await search_news(
        session=session,
        query=search.query,
        page=pagination.page,
        page_size=pagination.page_size,
        start_date=date_filter.start_date,
        end_date=date_filter.end_date,
        coin_symbol=coin_filter.coin
    )
    
    # Calculate pagination metadata
    total_pages = math.ceil(total_count / pagination.page_size) if total_count > 0 else 0
    has_next = pagination.page < total_pages
    has_prev = pagination.page > 1
    
    # Load ALL bookmarks for these posts in ONE query instead of N queries
    from app.models.bookmark import PostBookmark
    post_ids = [post.id for post in posts]
    bookmarks_stmt = select(PostBookmark.post_id).where(
        PostBookmark.user_id == current_user.id,
        PostBookmark.post_id.in_(post_ids)
    )
    result = await session.execute(bookmarks_stmt)
    bookmarked_post_ids = set(result.scalars().all())
    
    # Use Pydantic's from_attributes properly
    post_items = []
    for post in posts:
        # Use SQLModel's built-in Pydantic integration
        post_schema = PostSchema.model_validate(post, from_attributes=True)
        
        # Transform post_coins to coins using the proper method
        post_schema.coins = [
            CoinResponse.from_post_coin(post_coin) 
            for post_coin in post.post_coins
        ]
        
        # Override only the bookmark status
        post_schema.is_bookmarked = post.id in bookmarked_post_ids
        
        post_items.append(post_schema)

    return NewsFeedResponse(
        page=pagination.page,
        page_size=pagination.page_size,
        total=total_count,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev,
        items=post_items
    )


@router.get("/{post_id}", response_model=PostSchema)
async def get_post(
    session: AsyncSessionDep,
    current_user: CurrentUserDep,
    post_id: int
) -> PostSchema:
    """Get a post by its ID"""
    post = await get_post_by_id(session=session, post_id=post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Use SQLModel's built-in Pydantic integration
    post_schema = PostSchema.model_validate(post, from_attributes=True)
    
    # Transform post_coins to coins using the proper method
    post_schema.coins = [
        CoinResponse.from_post_coin(post_coin) 
        for post_coin in post.post_coins
    ]
    
    # Override only the bookmark status
    post_schema.is_bookmarked = await is_bookmarked(
        session=session, user_id=current_user.id, post_id=post.id)
    
    return post_schema
