from datetime import datetime
from typing import List, Optional, TYPE_CHECKING, Dict, Any

from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import UniqueConstraint

from app.models.base import Base
from app.models.coin import Coin

if TYPE_CHECKING:
    from app.models.bookmark import NewsBookmark


class NewsItem(Base, table=True):
    __tablename__ = "news_items"

    feed: str = "Sentix"
    item_type: str = Field(index=True)  # 'article' or 'post'
    source: str = Field(index=True)
    url: str = Field(unique=True, index=True)
    icon_url: Optional[str] = None
    title: str = Field(index=True)
    body: Optional[str] = None
    image_url: Optional[str] = None
    time: datetime = Field(index=True)
    sentiment: str = Field(index=True)
    score: float = Field(index=True)

    coins: List["NewsCoin"] = Relationship(back_populates="news_item")
    bookmarks: List["NewsBookmark"] = Relationship(back_populates="news_item")
    
    @property
    def is_article(self) -> bool:
        return self.item_type == "article"
    
    @property
    def is_post(self) -> bool:
        return self.item_type == "post"
        
    def get_formatted_coins(self) -> List[Dict[str, Any]]:
        """Return a formatted list of coins directly usable in API responses"""
        coin_list = []
        for news_coin in self.coins:
            if not news_coin.coin:
                continue
                
            coin_list.append({
                "id": news_coin.coin.id,
                "symbol": news_coin.coin.symbol,
                "name": news_coin.coin.name,
                "image_url": news_coin.coin.image_url
            })
        return coin_list


class NewsCoin(SQLModel, table=True):
    __tablename__ = "news_coins"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    news_item_id: int = Field(foreign_key="news_items.id")
    coin_id: int = Field(foreign_key="coins.id")
    
    # Add constraint to enforce uniqueness between posts and coins
    __table_args__ = (
        UniqueConstraint("news_item_id", "coin_id", name="unique_news_coin"),
    )
    
    news_item: NewsItem = Relationship(back_populates="coins")
    coin: Coin = Relationship(back_populates="news_items")
