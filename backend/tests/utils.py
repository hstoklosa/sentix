"""
Utility functions and helpers for tests.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.coin import Coin
from app.models.post import Post
from app.models.post_coin import PostCoin


def create_sample_user_data(
    email: str = "test@example.com",
    username: str = "testuser",
    password: str = "TestPass123!",
    full_name: str = "Test User"
) -> Dict[str, str]:
    """Create sample user data for testing."""
    return {
        "email": email,
        "username": username,
        "password": password,
        "full_name": full_name
    }


def create_sample_post_data(
    title: str = "Test Post",
    body: str = "Test post body",
    url: str = "https://example.com/test",
    source: str = "TestSource",
    sentiment_score: float = 0.5,
    created_at: datetime = None
) -> Dict[str, Any]:
    """Create sample post data for testing."""
    return {
        "title": title,
        "body": body,
        "url": url,
        "source": source,
        "sentiment_score": sentiment_score,
        "created_at": created_at or datetime.utcnow()
    }


def create_sample_coin_data(
    symbol: str = "BTC",
    name: str = "Bitcoin",
    coingecko_id: str = "bitcoin"
) -> Dict[str, str]:
    """Create sample coin data for testing."""
    return {
        "symbol": symbol,
        "name": name,
        "coingecko_id": coingecko_id
    }


async def create_test_posts_with_timeline(
    session: AsyncSession,
    coin: Coin,
    days: int = 7,
    posts_per_day: int = 3
) -> List[Post]:
    """Create test posts with a timeline for sentiment divergence testing."""
    posts = []
    
    for day in range(days):
        date = datetime.utcnow() - timedelta(days=day)
        
        for post_num in range(posts_per_day):
            # Create posts with varying sentiment
            sentiment = 0.3 + (day * 0.1) + (post_num * 0.05)
            sentiment = min(sentiment, 1.0)  # Cap at 1.0
            
            post = Post(
                title=f"Test Post Day {day} #{post_num}",
                body=f"Test content for {coin.symbol} on day {day}",
                url=f"https://example.com/test-{day}-{post_num}",
                source="TestSource",
                sentiment_score=sentiment,
                created_at=date
            )
            session.add(post)
            posts.append(post)
    
    await session.commit()
    
    # Create PostCoin relationships
    for post in posts:
        await session.refresh(post)
        post_coin = PostCoin(post_id=post.id, coin_id=coin.id)
        session.add(post_coin)
    
    await session.commit()
    return posts


def mock_async_session_with_query_result(return_value):
    """Create a mock AsyncSession that returns specific query results."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = return_value
    mock_session.exec.return_value = mock_result
    return mock_session


def assert_pagination_response(response_data: Dict[str, Any], expected_total: int = None):
    """Assert that a response has proper pagination structure."""
    assert "items" in response_data
    assert "total" in response_data
    assert "page" in response_data
    assert "size" in response_data
    assert "has_next" in response_data
    assert "has_prev" in response_data
    
    if expected_total is not None:
        assert response_data["total"] == expected_total


def create_tree_news_message(
    title: str = "Test News",
    body: str = "Test news body",
    url: str = "https://example.com/test",
    source: str = "Twitter",
    coins: List[str] = None,
    timestamp: str = None
) -> Dict[str, Any]:
    """Create a sample TreeNews WebSocket message."""
    if coins is None:
        coins = ["BTC"]
    
    if timestamp is None:
        timestamp = str(int(datetime.utcnow().timestamp()))
    
    return {
        "id": "test123",
        "title": title,
        "body": body,
        "url": url,
        "source": source,
        "coins": coins,
        "time": timestamp
    }


def create_coindesk_article(
    title: str = "Test Article",
    excerpt: str = "Test excerpt",
    slug: str = "test-article",
    published_at: str = None,
    categories: List[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create a sample CoinDesk article."""
    if published_at is None:
        published_at = datetime.utcnow().isoformat() + "Z"
    
    if categories is None:
        categories = [{"name": "Bitcoin"}]
    
    return {
        "slug": slug,
        "title": title,
        "excerpt": excerpt,
        "publishedAt": published_at,
        "url": f"https://coindesk.com/{slug}",
        "categories": categories
    }
