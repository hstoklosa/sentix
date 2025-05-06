import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.core.news.news_manager import NewsManager, Connection
from app.core.news.types import NewsData, NewsProvider
from app.models.news import NewsItem


class MockProvider:
    """Mock implementation of a news provider for testing the NewsManager."""
    
    def __init__(self, name="MockProvider"):
        self.name = name
        self.connected = False
        self.callback = None
    
    async def connect(self, callback):
        self.connected = True
        self.callback = callback
    
    async def disconnect(self):
        self.connected = False
        self.callback = None
    
    async def emit_news(self, news_data):
        """Send test news through the callback."""
        if self.connected and self.callback:
            await self.callback(news_data)


class TestNewsManager:
    """Unit tests for the NewsManager class."""
    
    @pytest.fixture
    def reset_manager(self):
        """Reset the singleton NewsManager before and after each test."""
        # Reset before test
        NewsManager._instance = None
        yield
        # Reset after test
        NewsManager._instance = None
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        websocket = AsyncMock()
        websocket.send_json = AsyncMock()
        return websocket
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = MagicMock()
        user.id = 1
        user.username = "testuser"
        return user
    
    @pytest.fixture
    def mock_news_data(self):
        """Create mock news data for testing."""
        news = NewsData()
        news.source = "Test Source"
        news.icon = "https://example.com/icon.png"
        news.feed = "TestFeed"
        news.url = "https://example.com/article/1"
        news.title = "Test News"
        news.body = "This is a test news article"
        news.image = "https://example.com/image.jpg"
        news.time = datetime.now()
        news.is_reply = False
        news.is_self_reply = False
        news.is_quote = False
        news.is_retweet = False
        news.coins = {"BTC", "ETH"}
        return news
    
    @pytest.mark.asyncio
    async def test_singleton_pattern(self, reset_manager):
        """Test that NewsManager follows the singleton pattern."""
        manager1 = NewsManager.get_instance()
        manager2 = NewsManager.get_instance()
        
        # Both instances should be the same object
        assert manager1 is manager2
    
    @pytest.mark.asyncio
    async def test_add_client(self, reset_manager, mock_websocket):
        """Test adding a client to the manager."""
        manager = NewsManager.get_instance()
        
        # Override the initialize method to prevent actually connecting to providers
        manager.initialize = AsyncMock()
        
        # Add a client
        await manager.add_client(mock_websocket)
        
        # Verify client was added
        assert mock_websocket in manager.active_connections
        
        # Initialize should have been called
        manager.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_client(self, reset_manager, mock_websocket):
        """Test removing a client from the manager."""
        manager = NewsManager.get_instance()
        
        # Override initialize method
        manager.initialize = AsyncMock()
        
        # Add a client then remove it
        await manager.add_client(mock_websocket)
        await manager.remove_client(mock_websocket)
        
        # Verify client was removed
        assert mock_websocket not in manager.active_connections
    
    @pytest.mark.asyncio
    async def test_update_subscription(self, reset_manager, mock_websocket):
        """Test updating a client's subscription."""
        manager = NewsManager.get_instance()
        
        # Override initialize method
        manager.initialize = AsyncMock()
        
        # Add a test provider
        test_provider = MockProvider("TestFeed")
        manager.providers["TestFeed"] = test_provider
        
        # Add a client
        await manager.add_client(mock_websocket)
        
        # Update subscription
        subscription = await manager.update_subscription(mock_websocket, "TestFeed")
        
        # Verify subscription was updated
        assert subscription == "TestFeed"
        assert manager.active_connections[mock_websocket].current_subscription == "TestFeed"
    
    @pytest.mark.asyncio
    async def test_invalid_subscription(self, reset_manager, mock_websocket):
        """Test updating subscription with invalid provider name."""
        manager = NewsManager.get_instance()
        
        # Override initialize method
        manager.initialize = AsyncMock()
        
        # Add a test provider
        test_provider = MockProvider("TestFeed")
        manager.providers["TestFeed"] = test_provider
        
        # Add a client
        await manager.add_client(mock_websocket)
        
        # Set initial subscription
        await manager.update_subscription(mock_websocket, "TestFeed")
        
        # Update to invalid subscription - should return current subscription
        subscription = await manager.update_subscription(mock_websocket, "InvalidFeed")
        
        # Verify subscription is still the original
        assert subscription == "TestFeed"
        assert manager.active_connections[mock_websocket].current_subscription == "TestFeed"
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, reset_manager, mock_websocket):
        """Test unsubscribing a client."""
        manager = NewsManager.get_instance()
        
        # Override initialize method
        manager.initialize = AsyncMock()
        
        # Add a client and subscribe
        await manager.add_client(mock_websocket)
        await manager.update_subscription(mock_websocket, "TestFeed")
        
        # Unsubscribe
        success = await manager.unsubscribe(mock_websocket)
        
        # Verify unsubscription
        assert success is True
        assert manager.active_connections[mock_websocket].current_subscription is None
    
    @pytest.mark.asyncio
    async def test_get_subscription(self, reset_manager, mock_websocket):
        """Test getting a client's subscription."""
        manager = NewsManager.get_instance()
        
        # Override initialize method
        manager.initialize = AsyncMock()
        
        # Add a client
        await manager.add_client(mock_websocket)
        
        # No subscription initially
        sub = await manager.get_subscription(mock_websocket)
        assert sub is None
        
        # Update subscription
        await manager.update_subscription(mock_websocket, "TestFeed")
        
        # Check subscription
        sub = await manager.get_subscription(mock_websocket)
        assert sub == "TestFeed"
    
    @pytest.mark.asyncio
    async def test_get_available_feeds(self, reset_manager):
        """Test getting available feeds."""
        manager = NewsManager.get_instance()
        
        # Add test providers
        manager.providers = {
            "Feed1": MockProvider("Feed1"),
            "Feed2": MockProvider("Feed2")
        }
        
        # Get feeds
        feeds = await manager.get_available_feeds()
        
        # Verify
        assert feeds == {"Feed1", "Feed2"}
    
    @pytest.mark.asyncio
    async def test_send_to_client(self, reset_manager, mock_websocket):
        """Test sending message to a client."""
        manager = NewsManager.get_instance()
        
        # Create connection
        connection = Connection(mock_websocket)
        
        # Send message
        message = {"type": "test", "data": "test_data"}
        success = await manager.send_to_client(mock_websocket, connection, message)
        
        # Verify
        assert success is True
        mock_websocket.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_send_to_client_failure(self, reset_manager, mock_websocket):
        """Test sending message to a client fails."""
        manager = NewsManager.get_instance()
        
        # Create connection
        connection = Connection(mock_websocket)
        
        # Make send_json raise an exception
        mock_websocket.send_json.side_effect = Exception("Connection lost")
        
        # Send message
        message = {"type": "test", "data": "test_data"}
        success = await manager.send_to_client(mock_websocket, connection, message)
        
        # Verify
        assert success is False
    
    @pytest.mark.asyncio
    @patch('app.core.news.news_manager.get_session')
    @patch('app.core.news.news_manager.save_news_item')
    @patch('app.core.news.news_manager.sentiment_analyser')
    async def test_on_news_received(self, mock_sentiment, mock_save, mock_get_session, 
                                    reset_manager, mock_news_data):
        """Test on_news_received callback."""
        # Setup
        manager = NewsManager.get_instance()
        manager.broadcast_to_clients = AsyncMock()
        
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value = iter([mock_session])
        
        # Mock sentiment analyzer
        mock_sentiment.predict.return_value = {"label": "positive", "score": 0.8}
        
        # Mock saved news item
        saved_news = MagicMock(spec=NewsItem)
        saved_news.id = 1
        saved_news.feed = "TestFeed"
        mock_save.return_value = saved_news
        
        # Call on_news_received
        await manager.on_news_received(mock_news_data, "TestFeed")
        
        # Verify
        mock_sentiment.predict.assert_called_once_with(mock_news_data.body)
        mock_save.assert_called_once()
        manager.broadcast_to_clients.assert_called_once_with(saved_news)
        assert mock_news_data.feed == "TestFeed"  # Feed should be updated
    
    @pytest.mark.asyncio
    async def test_connection_class(self):
        """Test the Connection class."""
        # Create a connection
        websocket = AsyncMock()
        user = MagicMock()
        user.username = "testuser"
        
        connection = Connection(websocket, user)
        
        # Verify attributes
        assert connection.websocket is websocket
        assert connection.user is user
        assert connection.connected_at is not None
        assert connection.current_subscription is None
        assert isinstance(connection.send_lock, asyncio.Lock)