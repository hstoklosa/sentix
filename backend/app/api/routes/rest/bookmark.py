from fastapi import APIRouter, status, HTTPException, Path

from app.deps import SessionDep, CurrentUserDep
from app.schemas.bookmark import (
    BookmarkCreate, 
    BookmarkResponse, 
)
from app.services import bookmark as bookmark_service

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


@router.post(
    "/", 
    response_model=BookmarkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bookmark a news item"
)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    user: CurrentUserDep,
    session: SessionDep
):
    """
    Create a bookmark for a news item.
    - news_item_id: ID of the news item to bookmark
    """
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
    session: SessionDep,
    news_item_id: int = Path(..., title="The ID of the news item to unbookmark"),
):
    """
    Remove a bookmark for a news item.
    
    - news_item_id: ID of the news item to unbookmark
    """
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
