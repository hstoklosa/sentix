import pytest
from datetime import datetime, timezone
from typing import Set
from sqlmodel.ext.asyncio.session import AsyncSession

from app.services.news import (
    get_or_create_coin,
    create_news_item,
    save_news_item,
    get_news_feed,
    get_post_by_id
)
from app.models.news import Coin, NewsItem
from app.core.news.types import NewsData

pytestmark = pytest.mark.asyncio

# Helper function to create NewsData for testing
def create_test_news_data(
    title: str = "Test Article",
    body: str = "This is a test article body",
    source: str = "Test Source",
    url: str = "https://test.com/article",
    coins: Set[str] = None
) -> NewsData:
    """Create test NewsData for testing"""
    news_data = NewsData()
    news_data.title = title
    news_data.body = body
    news_data.source = source
    news_data.time = datetime.now(timezone.utc)
    news_data.url = url
    news_data.image = "https://test.com/image.jpg"
    news_data.icon = "https://test.com/icon.jpg"
    news_data.feed = "test_feed"
    news_data.coins = coins if coins is not None else {"BTC", "ETH"}
    
    # Initialize Twitter-specific fields with defaults
    news_data.is_reply = False
    news_data.is_self_reply = False
    news_data.is_quote = False
    news_data.is_retweet = False
    
    return news_data

async def test_get_or_create_coin_new(session: AsyncSession):
    """Test creating a new coin"""
    coin = await get_or_create_coin(session, symbol="TEST")
    
    assert coin is not None
    assert coin.id is not None
    assert coin.symbol == "TEST"
    
    # Verify it was saved to the database
    all_coins = session.exec(Coin.select()).all()
    assert len(all_coins) == 1
    assert all_coins[0].symbol == "TEST"

async def test_get_or_create_coin_existing(session: AsyncSession):
    """Test getting an existing coin"""
    # Create coin first
    first_coin = await get_or_create_coin(session, symbol="TEST")
    
    # Get the same coin
    second_coin = await get_or_create_coin(session, symbol="TEST")
    
    assert second_coin is not None
    assert second_coin.id == first_coin.id
    assert second_coin.symbol == "TEST"
    
    # Verify only one record exists
    all_coins = session.exec(Coin.select()).all()
    assert len(all_coins) == 1

async def test_create_news_item_article(session: AsyncSession):
    """Test creating a news article"""
    news_data = create_test_news_data(
        title="Test Article",
        source="CoinDesk",
        url="https://test.com/unique-article"
    )
    
    item = await create_news_item(session, news_data)
    
    assert item is not None
    assert item.id is not None
    assert item.title == "Test Article"
    assert item.url == "https://test.com/unique-article"
    assert item.source == news_data.source
    assert item.time == news_data.time
    assert item.item_type == "article"  # Should be article for non-Twitter sources
    assert item.is_article is True
    assert item.is_post is False
    
    # Verify coin relationships were created
    article_coins = [nc.coin.symbol for nc in item.coins]
    assert set(article_coins) == {"BTC", "ETH"}

async def test_create_news_item_post(session: AsyncSession):
    """Test creating a social post"""
    news_data = create_test_news_data(
        title="Test Post",
        source="Twitter",
        url="https://twitter.com/test/status/123456"
    )
    # Add Twitter-specific fields
    news_data.is_reply = True
    news_data.is_quote = True
    
    item = await create_news_item(session, news_data)
    
    assert item is not None
    assert item.id is not None
    assert item.title == "Test Post"
    assert item.url == "https://twitter.com/test/status/123456"
    assert item.source == "Twitter"
    assert item.item_type == "post"  # Should be post for Twitter source
    assert item.is_article is False
    assert item.is_post is True
    
    # Verify coin relationships were created
    post_coins = [nc.coin.symbol for nc in item.coins]
    assert set(post_coins) == {"BTC", "ETH"}

async def test_save_news_item_article(session: AsyncSession):
    """Test saving a news article"""
    news_data = create_test_news_data(
        title="Test Article",
        source="CoinDesk",
        url="https://coindesk.com/test-article"
    )
    
    item = await save_news_item(session, news_data)
    
    assert item is not None
    assert item.item_type == "article"
    assert item.title == "Test Article"
    assert item.source == "CoinDesk"
    
    # Try saving again with same URL - should return existing item
    duplicate_data = create_test_news_data(
        title="Different Title",
        source="CoinDesk",
        url="https://coindesk.com/test-article"  # Same URL
    )
    
    duplicate_item = await save_news_item(session, duplicate_data)
    
    assert duplicate_item.id == item.id
    assert duplicate_item.title == "Test Article"  # Original title preserved

async def test_save_news_item_post(session: AsyncSession):
    """Test saving a social media post"""
    news_data = create_test_news_data(
        title="Test Tweet",
        source="Twitter",
        url="https://twitter.com/test/status/654321"
    )
    
    item = await save_news_item(session, news_data)
    
    assert item is not None
    assert item.item_type == "post"
    assert item.title == "Test Tweet"
    assert item.source == "Twitter"

async def test_get_news_feed(session: AsyncSession):
    """Test getting a paginated news feed"""
    # Create multiple news items with different dates
    for i in range(5):
        article_data = create_test_news_data(
            title=f"Article {i}",
            url=f"https://example.com/article-{i}",
            source="News Source"
        )
        # Set published_at to different times
        article_data.time = datetime(2023, 1, i+1, tzinfo=timezone.utc)
        await save_news_item(session, article_data)
    
    for i in range(5):
        post_data = create_test_news_data(
            title=f"Post {i}",
            url=f"https://twitter.com/status-{i}",
            source="Twitter"
        )
        # Set published_at to different times (interleaved with articles)
        post_data.time = datetime(2023, 1, i+1, 12, tzinfo=timezone.utc)
        await save_news_item(session, post_data)
    
    # Test pagination - page 1 with 3 items per page
    items, total = await get_news_feed(session, page=1, page_size=3)
    
    assert len(items) == 3
    assert total == 10
    
    # Verify ordering by published_at (newest first)
    assert items[0].time > items[1].time
    assert items[1].time > items[2].time
    
    # Test pagination - page 2 with 3 items per page
    page2_items, _ = await get_news_feed(session, page=2, page_size=3)
    
    assert len(page2_items) == 3
    assert page2_items[0].time < items[2].time
    
    # Test with larger page size
    all_items, _ = await get_news_feed(session, page=1, page_size=20)
    
    assert len(all_items) == 10  # Should return all items 

async def test_get_post_by_id(session: AsyncSession):
    """Test getting a news item by ID"""
    # Create a test article
    article_data = create_test_news_data(
        title="Test Get By ID",
        url="https://example.com/get-by-id",
        source="News Source"
    )
    saved_item = await save_news_item(session, article_data)
    
    # Get the item by ID
    retrieved_item = await get_post_by_id(session, saved_item.id)
    
    assert retrieved_item is not None
    assert retrieved_item.id == saved_item.id
    assert retrieved_item.title == "Test Get By ID"
    assert retrieved_item.url == "https://example.com/get-by-id"
    
    # Test with non-existent ID
    non_existent = await get_post_by_id(session, 9999)
    assert non_existent is None 