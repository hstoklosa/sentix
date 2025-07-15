from datetime import datetime
from typing import List, Optional, TYPE_CHECKING, Dict, Any

from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from app.models.coin import Coin
    from app.models.news import NewsItem


class PostCoin(SQLModel, table=True):
    __tablename__ = "post_coins"
    
    news_item_id: int = Field(foreign_key="news_items.id", primary_key=True)
    coin_id: int = Field(foreign_key="coins.id", primary_key=True)
    price_usd: Optional[float] = Field(default=None)
    price_timestamp: Optional[datetime] = Field(default=None)
    
    # Relationships
    news_item: "NewsItem" = Relationship(back_populates="post_coins")
    coin: "Coin" = Relationship()
