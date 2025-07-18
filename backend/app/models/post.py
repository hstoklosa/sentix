from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship

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
