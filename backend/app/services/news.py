import logging
from typing import List, Optional, Set, Union
from datetime import datetime

from sqlmodel import Session, select

from app.models.news import Coin, NewsArticle, SocialPost, NewsCoin
from app.core.news.types import NewsData

logger = logging.getLogger(__name__)

async def get_or_create_coin(session: Session, symbol: str) -> Coin:
    """
    Get a coin by symbol or create it if it doesn't exist
    
    Args:
        session: The database session
        symbol: The coin symbol
    
    Returns:
        The coin object
    """
    stmt = select(Coin).where(Coin.symbol == symbol)
    coin = session.exec(stmt).first()
    
    if not coin:
        coin = Coin(symbol=symbol)
        session.add(coin)
        session.commit()
        session.refresh(coin)
        logger.info(f"Created new coin: {symbol}")
    
    return coin


async def create_news_article(session: Session, news_data: NewsData) -> NewsArticle:
    """
    Create a news article
    
    Args:
        session: The database session
        news_data: The news data from TreeNews
    
    Returns:
        The created news article
    """
    # Create the article
    article = NewsArticle(
        title=news_data.title,
        body=news_data.body or "",
        source=news_data.source,
        published_at=news_data.time,
        url=news_data.url,
        image_url=news_data.image,
        icon_url=news_data.icon,
        feed_type=news_data.feed
    )
    
    session.add(article)
    session.commit()
    session.refresh(article)
    logger.info(f"Created news article: {article.id} - {article.title}")
    
    # Add coin relationships if any
    if news_data.coin:
        await add_coins_to_news(session, article=article, post=None, coin_symbols=news_data.coin)
    
    return article


async def create_social_post(session: Session, news_data: NewsData) -> SocialPost:
    """
    Create a social media post
    
    Args:
        session: The database session
        news_data: The news data from TreeNews
    
    Returns:
        The created social post
    """
    # Create the post
    post = SocialPost(
        title=news_data.title,
        body=news_data.body or "",
        source=news_data.source,
        published_at=news_data.time,
        url=news_data.url,
        image_url=news_data.image,
        icon_url=news_data.icon,
        feed_type=news_data.feed,
        is_reply=getattr(news_data, 'is_reply', False),
        is_self_reply=getattr(news_data, 'is_self_reply', False),
        is_quote=getattr(news_data, 'is_quote', False),
        is_retweet=getattr(news_data, 'is_retweet', False)
    )
    
    session.add(post)
    session.commit()
    session.refresh(post)
    logger.info(f"Created social post: {post.id} - {post.title}")
    
    # Add coin relationships if any
    if news_data.coin:
        await add_coins_to_news(session, article=None, post=post, coin_symbols=news_data.coin)
    
    return post


async def add_coins_to_news(
    session: Session, 
    article: Optional[NewsArticle] = None, 
    post: Optional[SocialPost] = None, 
    coin_symbols: Set[str] = None
) -> None:
    """
    Add coins to a news article or social post
    
    Args:
        session: The database session
        article: The news article (if adding to an article)
        post: The social post (if adding to a post)
        coin_symbols: Set of coin symbols to add
    """
    if not coin_symbols:
        return
        
    for symbol in coin_symbols:
        coin = await get_or_create_coin(session, symbol)
        
        if article:
            news_coin = NewsCoin(article_id=article.id, coin_id=coin.id)
            logger.debug(f"Adding coin {symbol} to article {article.id}")
        elif post:
            news_coin = NewsCoin(post_id=post.id, coin_id=coin.id)
            logger.debug(f"Adding coin {symbol} to post {post.id}")
        else:
            continue  # Skip if neither article nor post is provided
            
        session.add(news_coin)
    
    session.commit()


async def save_news_item(session: Session, news_data: NewsData) -> Union[NewsArticle, SocialPost]:
    """
    Save a news item (article or social post) based on its source
    
    Args:
        session: The database session
        news_data: The news data from TreeNews
    
    Returns:
        The created news article or social post
    """
    try:
        # Check if the URL already exists to avoid duplicates
        article_stmt = select(NewsArticle).where(NewsArticle.url == news_data.url)
        existing_article = session.exec(article_stmt).first()
        if existing_article:
            logger.info(f"News article already exists: {existing_article.id} - {existing_article.title}")
            return existing_article
            
        post_stmt = select(SocialPost).where(SocialPost.url == news_data.url)
        existing_post = session.exec(post_stmt).first()
        if existing_post:
            logger.info(f"Social post already exists: {existing_post.id} - {existing_post.title}")
            return existing_post
        
        # Create new item based on source
        if news_data.source == "Twitter":
            return await create_social_post(session, news_data)
        else:
            return await create_news_article(session, news_data)
    except Exception as e:
        logger.error(f"Error saving news item: {str(e)}")
        # Re-raise the exception for the caller to handle
        raise
