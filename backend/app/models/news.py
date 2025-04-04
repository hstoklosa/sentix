from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import UniqueConstraint

from app.models.base import Base

class Coin(Base, table=True):
    """Table to store cryptocurrency coins/tokens"""
    __tablename__ = "coins"
    
    symbol: str = Field(unique=True, index=True)
    name: Optional[str] = None
    
    # Relationships
    news_items: List["NewsCoin"] = Relationship(back_populates="coin")


class NewsBase(Base):
    """Base model for news items (articles and posts)"""
    title: str = Field(index=True)
    body: Optional[str] = None
    source: str = Field(index=True)
    time: datetime = Field(index=True)
    url: str = Field(unique=True, index=True)
    image_url: Optional[str] = None
    icon_url: Optional[str] = None
    feed_type: Optional[str] = None


class NewsArticle(NewsBase, table=True):
    """Model for news articles from publications"""
    __tablename__ = "news_articles"
    
    # Relationships
    coins: List["NewsCoin"] = Relationship(back_populates="article")


class SocialPost(NewsBase, table=True):
    """Model for social media posts (Twitter/X)"""
    __tablename__ = "social_posts"
    
    is_reply: bool = Field(default=False)
    is_self_reply: bool = Field(default=False)
    is_quote: bool = Field(default=False)
    is_retweet: bool = Field(default=False)
    
    # Relationships
    coins: List["NewsCoin"] = Relationship(back_populates="post")


class NewsCoin(SQLModel, table=True):
    """Association table for many-to-many relationship between news and coins"""
    __tablename__ = "news_coins"
    
    # Add a standalone primary key
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Make these regular foreign keys, not part of the primary key
    article_id: Optional[int] = Field(
        default=None, foreign_key="news_articles.id", nullable=True
    )
    post_id: Optional[int] = Field(
        default=None, foreign_key="social_posts.id", nullable=True
    )
    coin_id: int = Field(foreign_key="coins.id")
    
    # Add a unique constraint to enforce uniqueness between article/post and coin
    __table_args__ = (
        UniqueConstraint("article_id", "post_id", "coin_id", name="unique_news_coin"),
    )
    
    # Relationships
    article: Optional[NewsArticle] = Relationship(back_populates="coins")
    post: Optional[SocialPost] = Relationship(back_populates="coins")
    coin: Coin = Relationship(back_populates="news_items")
