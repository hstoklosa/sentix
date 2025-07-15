from datetime import datetime
from typing import List, Optional, TYPE_CHECKING, Dict, Any

from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from app.models.coin import Coin
    from app.models.post import Post


class PostCoin(SQLModel, table=True):
    __tablename__ = "post_coins"
    
    post_id: int = Field(foreign_key="posts.id", primary_key=True)
    coin_id: int = Field(foreign_key="coins.id", primary_key=True)
    price_usd: Optional[float] = Field(default=None)
    price_timestamp: Optional[datetime] = Field(default=None)
    
    # # Relationships
     
    post: "Post" = Relationship(back_populates="post_coins")
    coin: "Coin" = Relationship(
        back_populates="post_coins",  
        sa_relationship_kwargs={"lazy": "selectin"} # joined
    )