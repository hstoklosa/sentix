"""
Main conftest.py file containing shared fixtures for all tests.
"""
import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel, create_engine

from app.core.config import settings
from app.core.database import get_db_session
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.user import User
from app.models.coin import Coin
from app.models.post import Post
from app.models.post_coin import PostCoin
from app.models.bookmark import PostBookmark
from app.models.token import Token


# Test Database Configuration - Use in-memory database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)


@pytest_asyncio.fixture(scope="function")
async def setup_test_database():
    """Create test database tables."""
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    # Cleanup after all tests
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(setup_test_database) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        yield session
        await session.rollback()


@pytest.fixture
def override_get_db(db_session):
    """Override the database dependency for tests."""
    async def _override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db_session] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Create an HTTP client for integration tests."""
    from fastapi.testclient import TestClient
    from httpx import ASGITransport
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# Mock fixtures for external dependencies
@pytest.fixture
def mock_async_session():
    """Mock AsyncSession for unit tests."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_coingecko_client():
    """Mock CoinGecko client."""
    mock = MagicMock()
    mock.get_coins_list = AsyncMock(return_value=[
        {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
        {"id": "ethereum", "symbol": "eth", "name": "Ethereum"}
    ])
    mock.get_coin_market_data = AsyncMock(return_value={
        "market_cap": 1000000000,
        "volume_24h": 50000000,
        "price_change_percentage_24h": 2.5
    })
    return mock


@pytest.fixture
def mock_cmc_client():
    """Mock CoinMarketCap client."""
    mock = MagicMock()
    mock.get_global_metrics = AsyncMock(return_value={
        "total_market_cap": 2000000000000,
        "total_volume_24h": 100000000000,
        "bitcoin_dominance": 45.5
    })
    return mock


@pytest.fixture
def mock_ccxt_client():
    """Mock CCXT client for chart data."""
    mock = MagicMock()
    mock.fetch_ohlcv = AsyncMock(return_value=[
        [1640995200000, 47000, 48000, 46500, 47500, 1000],  # Sample OHLCV data
        [1641081600000, 47500, 48500, 47000, 48000, 1200],
    ])
    return mock


# User fixtures
@pytest.fixture
def sample_user_data():
    """Sample user data for tests."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPass123!",
        "full_name": "Test User"
    }


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, sample_user_data) -> User:
    """Create a test user in the database."""
    hashed_password = get_password_hash(sample_user_data["password"])
    user = User(
        email=sample_user_data["email"],
        username=sample_user_data["username"],
        password=hashed_password,  # User model uses 'password' field, not 'hashed_password'
        full_name=sample_user_data.get("full_name", "Test User")
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user: User) -> str:
    """Create an access token for the test user."""
    return create_access_token(subject=test_user.id)


# Coin fixtures
@pytest_asyncio.fixture
async def test_coin(db_session: AsyncSession) -> Coin:
    """Create a test coin in the database."""
    coin = Coin(
        symbol="BTC",
        name="Bitcoin",
        coingecko_id="bitcoin"
    )
    db_session.add(coin)
    await db_session.commit()
    await db_session.refresh(coin)
    return coin


@pytest_asyncio.fixture
async def test_coins(db_session: AsyncSession) -> list[Coin]:
    """Create multiple test coins in the database."""
    coins = [
        Coin(symbol="BTC", name="Bitcoin", coingecko_id="bitcoin"),
        Coin(symbol="ETH", name="Ethereum", coingecko_id="ethereum"),
        Coin(symbol="ADA", name="Cardano", coingecko_id="cardano"),
    ]
    for coin in coins:
        db_session.add(coin)
    await db_session.commit()
    for coin in coins:
        await db_session.refresh(coin)
    return coins


# Post fixtures
@pytest_asyncio.fixture
async def test_post(db_session: AsyncSession, test_coin: Coin) -> Post:
    """Create a test post in the database."""
    post = Post(
        title="Test Bitcoin News",
        body="This is a test post about Bitcoin price movement.",
        url="https://example.com/bitcoin-news",
        source="TestNews",
        item_type="article",
        feed="Sentix",
        sentiment="positive",
        score=0.75,
        time=datetime.now(timezone.utc)
    )
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)
    
    # Create PostCoin relationship
    post_coin = PostCoin(post_id=post.id, coin_id=test_coin.id)
    db_session.add(post_coin)
    await db_session.commit()
    
    # Refresh the post to load the relationships
    await db_session.refresh(post)
    
    return post


@pytest_asyncio.fixture
async def test_posts_with_sentiment(db_session: AsyncSession, test_coins: list[Coin]) -> list[Post]:
    """Create multiple test posts with varying sentiment scores."""
    posts = []
    
    # Create posts for the last 7 days
    for i in range(7):
        date = datetime.now(timezone.utc) - timedelta(days=i)
        
        # Bitcoin posts
        btc_post = Post(
            title=f"Bitcoin News Day {i}",
            body=f"Bitcoin analysis for day {i}",
            url=f"https://example.com/btc-{i}",
            source="TestNews",
            item_type="article",
            feed="Sentix",
            sentiment="positive" if i % 2 == 0 else "negative",
            score=0.5 + (i * 0.1),  # Varying sentiment
            time=date
        )
        db_session.add(btc_post)
        posts.append(btc_post)
        
        # Ethereum posts
        eth_post = Post(
            title=f"Ethereum News Day {i}",
            body=f"Ethereum analysis for day {i}",
            url=f"https://example.com/eth-{i}",
            source="TestNews",
            item_type="article",
            feed="Sentix",
            sentiment="neutral",
            score=0.3 + (i * 0.05),  # Different sentiment pattern
            time=date
        )
        db_session.add(eth_post)
        posts.append(eth_post)
    
    await db_session.commit()
    
    # Create PostCoin relationships
    btc_coin = test_coins[0]  # Bitcoin
    eth_coin = test_coins[1]  # Ethereum
    
    for i, post in enumerate(posts):
        if i % 2 == 0:  # Bitcoin posts
            post_coin = PostCoin(post_id=post.id, coin_id=btc_coin.id)
        else:  # Ethereum posts
            post_coin = PostCoin(post_id=post.id, coin_id=eth_coin.id)
        db_session.add(post_coin)
    
    await db_session.commit()
    return posts


@pytest_asyncio.fixture
async def test_posts_for_pagination(db_session: AsyncSession, test_coins: list[Coin]) -> list[Post]:
    """Create multiple test posts for pagination testing."""
    posts = []
    
    # Create 25 posts to test pagination (more than default page size of 20)
    for i in range(25):
        date = datetime.now(timezone.utc) - timedelta(hours=i)
        
        post = Post(
            title=f"Test Post {i+1}",
            body=f"This is test post number {i+1} for pagination testing.",
            url=f"https://example.com/post-{i+1}",
            source="TestNews",
            item_type="article",
            feed="Sentix",
            sentiment="positive" if i % 3 == 0 else "neutral" if i % 3 == 1 else "negative",
            score=0.1 + (i * 0.03),
            time=date
        )
        db_session.add(post)
        posts.append(post)
    
    await db_session.commit()
    
    # Create PostCoin relationships - alternate between Bitcoin and Ethereum
    btc_coin = test_coins[0]
    eth_coin = test_coins[1]
    
    for i, post in enumerate(posts):
        coin = btc_coin if i % 2 == 0 else eth_coin
        post_coin = PostCoin(post_id=post.id, coin_id=coin.id)
        db_session.add(post_coin)
    
    await db_session.commit()
    return posts


@pytest_asyncio.fixture
async def test_posts_for_search(db_session: AsyncSession, test_coins: list[Coin]) -> list[Post]:
    """Create test posts with specific content for search testing."""
    posts_data = [
        {
            "title": "Bitcoin reaches new heights",
            "body": "Bitcoin price analysis shows bullish trends in the cryptocurrency market.",
            "url": "https://example.com/bitcoin-heights",
        },
        {
            "title": "Ethereum smart contracts update",
            "body": "Latest developments in Ethereum blockchain technology and smart contracts.",
            "url": "https://example.com/ethereum-contracts",
        },
        {
            "title": "Market volatility concerns",
            "body": "Analysis of current market conditions and volatility patterns in crypto.",
            "url": "https://example.com/market-volatility",
        },
        {
            "title": "DeFi protocol innovations",
            "body": "New DeFi protocols are revolutionizing decentralized finance.",
            "url": "https://example.com/defi-innovations",
        },
        {
            "title": "Regulatory news and updates",
            "body": "Government regulations affecting cryptocurrency trading and adoption.",
            "url": "https://example.com/regulatory-news",
        }
    ]
    
    posts = []
    base_time = datetime.now(timezone.utc)
    
    for i, post_data in enumerate(posts_data):
        post = Post(
            title=post_data["title"],
            body=post_data["body"],
            url=post_data["url"],
            source="TestNews",
            item_type="article",
            feed="Sentix",
            sentiment="positive" if i % 2 == 0 else "negative",
            score=0.2 + (i * 0.15),
            time=base_time - timedelta(minutes=i * 10)
        )
        db_session.add(post)
        posts.append(post)
    
    await db_session.commit()
    
    # Create PostCoin relationships based on content
    btc_coin = test_coins[0]  # Bitcoin
    eth_coin = test_coins[1]  # Ethereum
    
    # Bitcoin-related posts (first and third)
    for i in [0, 2]:
        post_coin = PostCoin(post_id=posts[i].id, coin_id=btc_coin.id)
        db_session.add(post_coin)
    
    # Ethereum-related posts (second and fourth)
    for i in [1, 3]:
        post_coin = PostCoin(post_id=posts[i].id, coin_id=eth_coin.id)
        db_session.add(post_coin)
    
    await db_session.commit()
    return posts


# Bookmark fixtures
@pytest_asyncio.fixture
async def test_bookmark(db_session: AsyncSession, test_user: User, test_post: Post) -> PostBookmark:
    """Create a test bookmark in the database."""
    bookmark = PostBookmark(
        user_id=test_user.id,
        post_id=test_post.id
    )
    db_session.add(bookmark)
    await db_session.commit()
    await db_session.refresh(bookmark)
    return bookmark


# News data fixtures
@pytest.fixture
def sample_tree_news_message():
    """Sample TreeNews WebSocket message."""
    return {
        "id": "123456",
        "title": "Bitcoin Reaches New High",
        "body": "Bitcoin (BTC) has reached a new all-time high today, surpassing $50,000.",
        "url": "https://example.com/bitcoin-high",
        "source": "Twitter",
        "coins": ["BTC"],
        "time": "1640995200"
    }


@pytest.fixture
def sample_coindesk_article():
    """Sample CoinDesk article data."""
    return {
        "slug": "bitcoin-price-analysis",
        "title": "Bitcoin Price Analysis: Bulls Target $50K",
        "excerpt": "Technical analysis suggests Bitcoin could reach $50,000 soon.",
        "publishedAt": "2024-01-01T12:00:00Z",
        "url": "https://coindesk.com/bitcoin-price-analysis",
        "categories": [
            {"name": "Bitcoin"},
            {"name": "Price Analysis"}
        ]
    }


# Event loop is now handled automatically by pytest-asyncio
