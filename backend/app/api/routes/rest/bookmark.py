from fastapi import APIRouter, status, Depends, HTTPException, Path

from app.deps import AsyncSessionDep, CurrentUserDep
from app.schemas.bookmark import (
    BookmarkCreate, 
    BookmarkResponse, 
    BookmarkedNewsResponse
)
from app.schemas.pagination import PaginationParams
from app.services import bookmark as bookmark_service

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


@router.post(
    "/", 
    response_model=BookmarkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bookmark a news item"
)
async def create_bookmark(
    session: AsyncSessionDep,
    user: CurrentUserDep,
    bookmark_data: BookmarkCreate
):
    result = await bookmark_service.create_bookmark(
        session=session,
        user_id=user.id,
        news_item_id=bookmark_data.news_item_id
    )
    return result


@router.delete(
    "/{news_item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a bookmark"
)
async def delete_bookmark(
    user: CurrentUserDep,
    session: AsyncSessionDep,
    news_item_id: int = Path(..., title="The ID of the news item to unbookmark"),
):
    deleted = await bookmark_service.delete_bookmark(
        session=session,
        user_id=user.id,
        news_item_id=news_item_id
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )
    
    return None  # 204 No Content


@router.get(
    "/",
    response_model=BookmarkedNewsResponse,
    summary="Get user's bookmarked news items"
)
async def get_bookmarked_news(
    user: CurrentUserDep,
    session: AsyncSessionDep,
    pagination: PaginationParams = Depends(),
):
    items, total_count = await bookmark_service.get_user_bookmarks(
        session=session,
        user_id=user.id,
        page=pagination.page,
        page_size=pagination.page_size
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