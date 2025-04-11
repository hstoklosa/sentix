from datetime import datetime

from pydantic import BaseModel


class BookmarkCreate(BaseModel):
    """Schema for creating a news bookmark"""
    news_item_id: int


class BookmarkResponse(BaseModel):
    """Response schema for a bookmark operation"""
    user_id: int
    news_item_id: int
    created_at: datetime
    id: int
    
    class Config:
        from_attributes = True
