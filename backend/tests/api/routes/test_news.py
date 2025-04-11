import pytest
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock

from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.services.news import save_news_item
from app.core.news.types import NewsData
from app.models.news import NewsItem
from app.services.bookmark import add_bookmark, remove_bookmark

pytestmark = pytest.mark.asyncio

# Helper function to create test news data
def create_test_news_data(
    title: str,
    source: str,
    url: str,
    time: datetime = None,
    coins: set = None
) -> NewsData:
    """Create test news data for testing"""
    if time is None:
        time = datetime.now(timezone.utc)
    
    news_data = NewsData()
    news_data.title = title
    news_data.body = "Test body content"
    news_data.source = source
    news_data.time = time
    news_data.url = url
    news_data.image = "https://test.com/image.jpg"
    news_data.icon = "https://test.com/icon.png"
    news_data.feed = "test_feed"
    news_data.coins = coins if coins is not None else {"BTC", "ETH"}
    
    # Initialize Twitter-specific fields with defaults
    news_data.is_reply = False
    news_data.is_self_reply = False
    news_data.is_quote = False
    news_data.is_retweet = False
    
    return news_data

async def test_get_news_feed_empty(client: AsyncClient):
    """Test getting an empty news feed"""
    response = await client.get("/api/news/")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total"] == 0
    assert data["total_pages"] == 0
    assert data["has_next"] is False
    assert data["has_prev"] is False
    assert data["items"] == []

async def test_get_news_feed_with_data(client: AsyncClient, session: AsyncSession, authenticated_user):
    """Test getting a news feed with data"""
    # Create test articles and posts
    for i in range(3):
        article_data = create_test_news_data(
            title=f"Test Article {i}",
            source="News Source",
            url=f"https://example.com/article-{i}",
            time=datetime(2023, 1, i+1, tzinfo=timezone.utc),
        )
        await save_news_item(session, article_data)
    
    for i in range(3):
        post_data = create_test_news_data(
            title=f"Test Post {i}",
            source="Twitter",
            url=f"https://twitter.com/status-{i}",
            time=datetime(2023, 1, i+1, 12, tzinfo=timezone.utc),
        )
        await save_news_item(session, post_data)
    
    # Bookmark one article to test bookmark flag
    all_items = session.exec(NewsItem.select()).all()
    await add_bookmark(session, user_id=authenticated_user.id, news_item_id=all_items[0].id)
    
    # Get the news feed
    response = await client.get("/api/news/")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total"] == 6
    assert data["total_pages"] == 1
    assert data["has_next"] is False
    assert data["has_prev"] is False
    assert len(data["items"]) == 6
    
    # Verify the items are in the correct order (most recent first)
    items = data["items"]
    for i in range(len(items) - 1):
        assert items[i]["time"] >= items[i+1]["time"]
    
    # Verify the content of the items
    assert any(item["title"] == "Test Article 0" for item in items)
    assert any(item["title"] == "Test Post 0" for item in items)
    
    # Verify item type
    for item in items:
        if "Test Article" in item["title"]:
            assert item["_type"] == "article"
        elif "Test Post" in item["title"]:
            assert item["_type"] == "post"
    
    # Verify bookmark status is included
    bookmarked_items = [item for item in items if item["is_bookmarked"] is True]
    assert len(bookmarked_items) == 1
    
    # Verify coins are included
    for item in items:
        assert len(item["coins"]) == 2
        coin_symbols = {coin["symbol"] for coin in item["coins"]}
        assert coin_symbols == {"BTC", "ETH"}

async def test_get_news_feed_pagination(client: AsyncClient, session: AsyncSession, authenticated_user):
    """Test news feed pagination"""
    # Create 10 test articles with different dates
    for i in range(10):
        article_data = create_test_news_data(
            title=f"Pagination Article {i}",
            source="News Source",
            url=f"https://example.com/pagination-{i}",
            time=datetime(2023, 1, 10-i, tzinfo=timezone.utc),  # Newest first
        )
        await save_news_item(session, article_data)
    
    # Test first page with 3 items
    response = await client.get("/api/news/?page=1&page_size=3")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 3
    assert data["total"] == 10
    assert data["total_pages"] == 4  # Ceiling of 10/3
    assert data["has_next"] is True
    assert data["has_prev"] is False
    assert len(data["items"]) == 3
    
    # Items should be ordered by date (newest first)
    first_page_items = data["items"]
    assert first_page_items[0]["title"] == "Pagination Article 0"
    assert first_page_items[1]["title"] == "Pagination Article 1"
    assert first_page_items[2]["title"] == "Pagination Article 2"
    
    # Test second page
    response = await client.get("/api/news/?page=2&page_size=3")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["page"] == 2
    assert len(data["items"]) == 3
    assert data["has_next"] is True
    assert data["has_prev"] is True
    
    # Verify second page items
    second_page_items = data["items"]
    assert second_page_items[0]["title"] == "Pagination Article 3"
    
    # Test last page
    response = await client.get("/api/news/?page=4&page_size=3")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["page"] == 4
    assert len(data["items"]) == 1  # Only 1 item on the last page (10th item)
    assert data["has_next"] is False
    assert data["has_prev"] is True

async def test_get_news_feed_invalid_pagination(client: AsyncClient):
    """Test news feed with invalid pagination parameters"""
    # Test with negative page
    response = await client.get("/api/news/?page=-1")
    assert response.status_code == 422
    
    # Test with zero page
    response = await client.get("/api/news/?page=0")
    assert response.status_code == 422
    
    # Test with negative page size
    response = await client.get("/api/news/?page_size=-1")
    assert response.status_code == 422
    
    # Test with zero page size
    response = await client.get("/api/news/?page_size=0")
    assert response.status_code == 422
    
    # Test with too large page size
    response = await client.get("/api/news/?page_size=101")
    assert response.status_code == 422

async def test_get_post_by_id(client: AsyncClient, session: AsyncSession, authenticated_user):
    """Test getting a news item by ID"""
    # Create a test article
    article_data = create_test_news_data(
        title="Test Single Post",
        source="News Source",
        url="https://example.com/single-post",
        time=datetime(2023, 1, 1, tzinfo=timezone.utc)
    )
    saved_item = await save_news_item(session, article_data)
    
    # Get the post by ID
    response = await client.get(f"/api/news/{saved_item.id}")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == saved_item.id
    assert data["title"] == "Test Single Post"
    assert data["_type"] == "article"
    assert data["is_bookmarked"] is False
    
    # Verify coins are included
    assert len(data["coins"]) == 2
    coin_symbols = {coin["symbol"] for coin in data["coins"]}
    assert coin_symbols == {"BTC", "ETH"}
    
    # Test with bookmarked post
    await add_bookmark(session, user_id=authenticated_user.id, news_item_id=saved_item.id)
    
    response = await client.get(f"/api/news/{saved_item.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["is_bookmarked"] is True
    
    # Test with non-existent ID
    response = await client.get("/api/news/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found" 