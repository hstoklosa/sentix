import pytest
from datetime import datetime, timezone
from app.core.news.types import NewsData, NewsProvider


def test_news_data_creation():
    """Test creating a NewsData instance with all fields."""
    now = datetime.now(timezone.utc)
    news = NewsData()
    news.source = "CoinDesk"
    news.icon = "https://coindesk.com/icon.png"
    news.feed = "cryptocurrency"
    news.url = "https://coindesk.com/article/1"
    news.title = "Bitcoin Reaches New High"
    news.body = "Bitcoin has reached a new all-time high..."
    news.image = "https://coindesk.com/images/bitcoin.jpg"
    news.time = now
    news.is_reply = False
    news.is_self_reply = False
    news.is_quote = False
    news.is_retweet = False
    news.coins = {"BTC", "ETH"}
    
    assert news.source == "CoinDesk"
    assert news.icon == "https://coindesk.com/icon.png"
    assert news.feed == "cryptocurrency"
    assert news.url == "https://coindesk.com/article/1"
    assert news.title == "Bitcoin Reaches New High"
    assert news.body == "Bitcoin has reached a new all-time high..."
    assert news.image == "https://coindesk.com/images/bitcoin.jpg"
    assert news.time == now
    assert news.is_reply is False
    assert news.is_self_reply is False
    assert news.is_quote is False
    assert news.is_retweet is False
    assert news.coins == {"BTC", "ETH"}


class MockNewsProvider:
    """Mock implementation of the NewsProvider protocol for testing."""
    
    def __init__(self):
        self.connected = False
        self.callback = None
        self.news_items = []
    
    async def connect(self, callback):
        """Connect to mock news source and store the callback."""
        self.connected = True
        self.callback = callback
    
    async def disconnect(self):
        """Disconnect from mock news source."""
        self.connected = False
        self.callback = None
    
    async def emit_news(self, news_data):
        """Simulate receiving news by calling the stored callback."""
        if self.callback and self.connected:
            self.news_items.append(news_data)
            await self.callback(news_data)


@pytest.mark.asyncio
async def test_news_provider_protocol():
    """Test that a class implementing the NewsProvider protocol works correctly."""
    # Create a mock news provider
    provider = MockNewsProvider()
    assert provider.connected is False
    
    # Create a callback function that stores received news
    received_news = []
    async def news_callback(news_data):
        received_news.append(news_data)
    
    # Connect to the provider
    await provider.connect(news_callback)
    assert provider.connected is True
    assert provider.callback is news_callback
    
    # Create and emit a news item
    news = NewsData()
    news.source = "Test Source"
    news.title = "Test News"
    news.body = "Test content"
    news.url = "https://example.com/news"
    news.time = datetime.now(timezone.utc)
    news.coins = {"BTC"}
    
    await provider.emit_news(news)
    
    # Check that callback was called
    assert len(received_news) == 1
    assert received_news[0].source == "Test Source"
    assert received_news[0].title == "Test News"
    
    # Disconnect
    await provider.disconnect()
    assert provider.connected is False
    
    # After disconnect, callback shouldn't be called
    news2 = NewsData()
    news2.title = "News after disconnect"
    await provider.emit_news(news2)
    assert len(received_news) == 1  # Still only 1 item