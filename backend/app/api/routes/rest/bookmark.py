from fastapi import APIRouter, status, Depends, HTTPException, Path
from typing import Optional

from app.deps import AsyncSessionDep, CurrentUserDep
from app.schemas.bookmark import (
    BookmarkCreate, 
    BookmarkResponse, 
    BookmarkedPostsResponse
)
from app.schemas.pagination import PaginationParams
from app.schemas.news import DateFilterParams, CoinFilterParams
from app.services import bookmark as bookmark_service

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


@router.post(
    "/", 
    response_model=BookmarkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bookmark a post"
)
async def create_bookmark(
    session: AsyncSessionDep,
    user: CurrentUserDep,
    bookmark_data: BookmarkCreate
):
    result = await bookmark_service.create_bookmark(
        session=session,
        user_id=user.id,
        post_id=bookmark_data.post_id
    )
    return result


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a bookmark"
)
async def delete_bookmark(
    user: CurrentUserDep,
    session: AsyncSessionDep,
    post_id: int = Path(..., title="The ID of the post item to unbookmark"),
):
    deleted = await bookmark_service.delete_bookmark(
        session=session,
        user_id=user.id,
        post_id=post_id
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )
    
    return None  # 204 No Content


@router.get(
    "/",
    response_model=BookmarkedPostsResponse,
    summary="Get user's bookmarked posts"
)
async def get_bookmarked_posts(
    user: CurrentUserDep,
    session: AsyncSessionDep,
    pagination: PaginationParams = Depends(),
    date_filter: DateFilterParams = Depends(),
    coin_filter: CoinFilterParams = Depends(),
    query: Optional[str] = None,
):
    items, total_count = await bookmark_service.get_user_bookmarks(
        session=session,
        user_id=user.id,
        page=pagination.page,
        page_size=pagination.page_size,
        search_query=query,
        start_date=date_filter.start_date,
        end_date=date_filter.end_date,
        coin_symbol=coin_filter.coin
    )
    
    total_pages = (total_count + pagination.page_size - 1) // pagination.page_size
    has_next = pagination.page < total_pages
    has_prev = pagination.page > 1
    
    return {
        "page": pagination.page,
        "page_size": pagination.page_size,
        "total": total_count,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_prev": has_prev,
        "items": items
    } 