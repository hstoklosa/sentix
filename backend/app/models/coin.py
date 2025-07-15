from typing import List, Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship
from app.models.base import Base
from app.models.post_coin import PostCoin

if TYPE_CHECKING:
    from app.models.news import NewsItem

class Coin(Base, table=True):
    __tablename__ = "coins"
    
    name: str = Field(unique=True, index=True)
    symbol: str = Field(unique=True, index=True)
    image_url: Optional[str] = Field(default=None)

    news_items: List["NewsItem"] = Relationship(back_populates="coins", link_model=PostCoin)