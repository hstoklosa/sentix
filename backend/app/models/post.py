from datetime import datetime
from typing import List, Optional, TYPE_CHECKING, Dict, Any

from sqlmodel import Field, SQLModel, Relationship

from app.models.base import Base
from app.models.post_coin import PostCoin
from app.models.bookmark import PostBookmark

if TYPE_CHECKING:
    from app.models.coin import Coin
    from app.models.post_coin import PostCoin


class Post(Base, table=True):
    __tablename__ = "posts"

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

    post_coins: List["PostCoin"] = Relationship(
        back_populates="post",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"}
    )

    # Direct many-to-many relationship with coins
    coins: List["Coin"] = Relationship(
        back_populates="posts",
        link_model=PostCoin,
        sa_relationship_kwargs={"lazy": "selectin", "overlaps": "post_coins,coin,post"}
    )

    post_bookmarks: List[PostBookmark] = Relationship(
        back_populates="post",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"}
    )

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
