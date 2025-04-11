from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.news import NewsCoin


class Coin(Base, table=True):
    __tablename__ = "coins"
    
    symbol: str = Field(unique=True, index=True)
    name: Optional[str] = None

    news_items: List["NewsCoin"] = Relationship(back_populates="coin")