from typing import List
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.news import Post, PaginatedResponse


class BookmarkCreate(BaseModel):
    post_id: int


class BookmarkResponse(BaseModel):
    id: int
    user_id: int
    post_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class BookmarkedPost(Post):
    bookmark_id: int
    bookmarked_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class BookmarkedPostsResponse(PaginatedResponse):
    items: List[BookmarkedPost] 