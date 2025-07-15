from typing import List, Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship
from app.models.base import Base
from app.models.post_coin import PostCoin

if TYPE_CHECKING:
    from app.models.post import Post

class Coin(Base, table=True):
    __tablename__ = "coins"
    
    name: str = Field(unique=True, index=True)
    symbol: str = Field(unique=True, index=True)
    # coingecko_id: Optional[str] = Field(default=None, index=True)
    image_url: Optional[str] = Field(default=None)

    post_coins: List[PostCoin] = Relationship(
        back_populates="coin",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "overlaps": "coins"}
    )
    
    posts: List["Post"] = Relationship(
        back_populates="coins", 
        link_model=PostCoin, 
        sa_relationship_kwargs={"overlaps": "coin,post_coins,post"}
    )