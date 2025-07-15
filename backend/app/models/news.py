from datetime import datetime
from typing import List, Optional, TYPE_CHECKING, Dict, Any

from sqlmodel import Field, SQLModel, Relationship

from app.models.base import Base
from app.models.post_coin import PostCoin

if TYPE_CHECKING:
    from app.models.coin import Coin
    from app.models.bookmark import NewsBookmark
    from app.models.post_coin import PostCoin


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

    coins: List["Coin"] = Relationship(back_populates="news_items", link_model=PostCoin)
    post_coins: List["PostCoin"] = Relationship(back_populates="news_item")
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
        for post_coin in self.post_coins:
            if not post_coin.coin:
                continue
                
            coin_data = {
                "id": post_coin.coin.id,
                "symbol": post_coin.coin.symbol,
                "name": post_coin.coin.name,
                "image_url": post_coin.coin.image_url
            }
            
            # Add price information if available
            if post_coin.price_usd is not None:
                coin_data["price_usd"] = post_coin.price_usd
                if post_coin.price_timestamp:
                    coin_data["price_timestamp"] = post_coin.price_timestamp.isoformat()
            
            coin_list.append(coin_data)
        return coin_list
