import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.core.news.tree_news import TreeNews
from app.core.news.types import NewsData, DataSource


class TestTreeNewsHandleMessage:
    """Test the _handle_message method of TreeNews class."""

    @pytest.fixture
    def tree_news_instance(self):
        """Create a TreeNews instance for testing."""
        return TreeNews()

    @pytest.fixture
    def mock_callback(self):
        """Mock callback function for TreeNews."""
        return AsyncMock()

    @pytest.fixture
    def sample_twitter_message(self):
        """Sample Twitter message from TreeNews."""
        return {
            "id": "1234567890",
            "title": "🚀 #Bitcoin just broke $50,000! This is huge for crypto adoption! #BTC #crypto",
            "body": "The market is showing strong bullish momentum with institutional buying increasing.",
            "url": "https://twitter.com/cryptotrader/status/1234567890",
            "link": "https://twitter.com/cryptotrader/status/1234567890",
            "icon": "https://twitter.com/favicon.ico",
            "image": "https://pbs.twimg.com/media/chart.jpg",
            "time": 1640995200000,  # Unix timestamp in milliseconds
            "suggestions": [
                {"coin": "BTC"},
                {"coin": "ETH"}
            ],
            "info": {
                "isQuote": False,
                "isReply": False,
                "isRetweet": False,
                "isSelfReply": False
            }
        }

    @pytest.fixture
    def sample_blog_message(self):
        """Sample blog message from TreeNews."""
        return {
            "id": "blog123456",
            "title": "CoinDesk: Bitcoin Price Analysis Shows Bullish Pattern",
            "body": "Technical indicators suggest Bitcoin could reach new highs in the coming weeks.",
            "url": "https://coindesk.com/markets/bitcoin-price-analysis",
            "source": "Blogs",
            "icon": "https://coindesk.com/favicon.ico",
            "image": "https://coindesk.com/chart-image.png",
            "time": 1640995200000,
            "suggestions": [
                {"coin": "BTC"},
                {"coin": "ETH"},
                {"coin": "ADA"}
            ]
        }

    @pytest.fixture
    def sample_other_source_message(self):
        """Sample message from other source."""
        return {
            "id": "other123456",
            "title": "Ethereum Network Upgrade Successful",
            "body": "The latest Ethereum network upgrade has been successfully implemented.",
            "url": "https://ethereum.org/news/upgrade-complete",
            "source": "Official",
            "icon": "https://ethereum.org/favicon.ico",
            "time": 1640995200000,
            "suggestions": [
                {"coin": "ETH"}
            ]
        }

    @pytest.fixture
    def minimal_message(self):
        """Minimal message with required fields only."""
        return {
            "time": 1640995200000,
            "suggestions": []
        }

    @pytest.fixture
    def message_with_missing_fields(self):
        """Message with some missing optional fields."""
        return {
            "title": "Bitcoin News",
            "time": 1640995200000,
            "suggestions": [{"coin": "BTC"}],
            "url": "https://example.com/news"
            # Missing: body, image, icon, source, info
        }

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_message_twitter_source(self, tree_news_instance, mock_callback, sample_twitter_message):
        """Test _handle_message with Twitter source message."""
        tree_news_instance._callback = mock_callback
        
        # Mock environment settings
        with patch('app.core.news.tree_news.settings.ENVIRONMENT', 'test'):
            message_json = json.dumps(sample_twitter_message)
            await tree_news_instance._handle_message(message_json)

        # Verify callback was called
        mock_callback.assert_called_once()
        
        # Get the NewsData object passed to callback
        call_args = mock_callback.call_args[0]
        news_data = call_args[0]
        
        # Verify NewsData object properties
        assert isinstance(news_data, NewsData)
        assert news_data.feed == DataSource.TREE_NEWS
        assert news_data.source == "Twitter"
        assert news_data.title == sample_twitter_message["title"]
        assert news_data.body == sample_twitter_message["body"]
        assert news_data.url == sample_twitter_message["url"]
        assert news_data.icon == sample_twitter_message["icon"]
        assert news_data.image == sample_twitter_message["image"]
        
        # Verify timestamp conversion
        expected_time = datetime.fromtimestamp(1640995200, tz=timezone.utc)
        assert news_data.time == expected_time
        
        # Verify coin symbols extraction
        assert news_data.coins == {"BTC", "ETH"}
        
        # Verify Twitter-specific info fields
        assert news_data.is_quote is False
        assert news_data.is_reply is False
        assert news_data.is_retweet is False
        assert news_data.is_self_reply is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_message_blog_source(self, tree_news_instance, mock_callback, sample_blog_message):
        """Test _handle_message with Blog source message."""
        tree_news_instance._callback = mock_callback
        
        with patch('app.core.news.tree_news.settings.ENVIRONMENT', 'test'):
            message_json = json.dumps(sample_blog_message)
            await tree_news_instance._handle_message(message_json)

        mock_callback.assert_called_once()
        
        call_args = mock_callback.call_args[0]
        news_data = call_args[0]
        
        # Verify source processing for blogs
        assert news_data.source == "Coindesk"  # First part of title before ":"
        assert news_data.title == "Bitcoin Price Analysis Shows Bullish Pattern"  # Part after ":"
        assert news_data.feed == DataSource.TREE_NEWS
        assert news_data.coins == {"BTC", "ETH", "ADA"}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_message_other_source(self, tree_news_instance, mock_callback, sample_other_source_message):
        """Test _handle_message with other source types."""
        tree_news_instance._callback = mock_callback
        
        with patch('app.core.news.tree_news.settings.ENVIRONMENT', 'test'):
            message_json = json.dumps(sample_other_source_message)
            await tree_news_instance._handle_message(message_json)

        mock_callback.assert_called_once()
        
        call_args = mock_callback.call_args[0]
        news_data = call_args[0]
        
        # Verify other source processing
        assert news_data.source == "Other"
        assert news_data.title == sample_other_source_message["title"]
        assert news_data.coins == {"ETH"}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_message_no_source_defaults_to_twitter(self, tree_news_instance, mock_callback, minimal_message):
        """Test _handle_message when source is None, should default to Twitter."""
        tree_news_instance._callback = mock_callback
        
        with patch('app.core.news.tree_news.settings.ENVIRONMENT', 'test'):
            message_json = json.dumps(minimal_message)
            await tree_news_instance._handle_message(message_json)

        mock_callback.assert_called_once()
        
        call_args = mock_callback.call_args[0]
        news_data = call_args[0]
        
        # Should default to Twitter when source is None
        assert news_data.source == "Twitter"
        assert news_data.feed == DataSource.TREE_NEWS

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_message_with_missing_fields(self, tree_news_instance, mock_callback, message_with_missing_fields):
        """Test _handle_message with missing optional fields."""
        tree_news_instance._callback = mock_callback
        
        with patch('app.core.news.tree_news.settings.ENVIRONMENT', 'test'):
            message_json = json.dumps(message_with_missing_fields)
            await tree_news_instance._handle_message(message_json)

        mock_callback.assert_called_once()
        
        call_args = mock_callback.call_args[0]
        news_data = call_args[0]
        
        # Verify defaults for missing fields
        assert news_data.title == "Bitcoin News"
        assert news_data.body == ""  # Should default to empty string
        assert news_data.image == ""  # Should default to empty string
        assert news_data.icon == ""  # Should default to empty string
        assert news_data.source == "Twitter"  # Should default since source is None
        assert news_data.coins == {"BTC"}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_message_twitter_with_info_flags(self, tree_news_instance, mock_callback):
        """Test _handle_message with Twitter info flags set to True."""
        tree_news_instance._callback = mock_callback
        
        twitter_message_with_flags = {
            "title": "RT @user: This is a retweet",
            "time": 1640995200000,
            "suggestions": [],
            "info": {
                "isQuote": True,
                "isReply": True,
                "isRetweet": True,
                "isSelfReply": True
            }
        }
        
        with patch('app.core.news.tree_news.settings.ENVIRONMENT', 'test'):
            message_json = json.dumps(twitter_message_with_flags)
            await tree_news_instance._handle_message(message_json)

        mock_callback.assert_called_once()
        
        call_args = mock_callback.call_args[0]
        news_data = call_args[0]
        
        # Verify Twitter info flags are set correctly
        assert news_data.is_quote is True
        assert news_data.is_reply is True
        assert news_data.is_retweet is True
        assert news_data.is_self_reply is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_message_fallback_to_link_for_url(self, tree_news_instance, mock_callback):
        """Test _handle_message uses 'link' field if 'url' is not present."""
        tree_news_instance._callback = mock_callback
        
        message_with_link = {
            "title": "Test News",
            "link": "https://example.com/news-link",
            "time": 1640995200000,
            "suggestions": []
            # No 'url' field
        }
        
        with patch('app.core.news.tree_news.settings.ENVIRONMENT', 'test'):
            message_json = json.dumps(message_with_link)
            await tree_news_instance._handle_message(message_json)

        mock_callback.assert_called_once()
        
        call_args = mock_callback.call_args[0]
        news_data = call_args[0]
        
        # Should use 'link' field when 'url' is not available
        assert news_data.url == "https://example.com/news-link"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_message_fallback_to_en_for_title(self, tree_news_instance, mock_callback):
        """Test _handle_message uses 'en' field if 'title' is not present."""
        tree_news_instance._callback = mock_callback
        
        message_with_en = {
            "en": "English Title",
            "time": 1640995200000,
            "suggestions": []
            # No 'title' field
        }
        
        with patch('app.core.news.tree_news.settings.ENVIRONMENT', 'test'):
            message_json = json.dumps(message_with_en)
            await tree_news_instance._handle_message(message_json)

        mock_callback.assert_called_once()
        
        call_args = mock_callback.call_args[0]
        news_data = call_args[0]
        
        # Should use 'en' field when 'title' is not available
        assert news_data.title == "English Title"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_message_invalid_json(self, tree_news_instance, mock_callback):
        """Test _handle_message handles invalid JSON gracefully."""
        tree_news_instance._callback = mock_callback
        
        invalid_json = "{ invalid json structure"
        
        with patch('app.core.news.tree_news.logger') as mock_logger:
            await tree_news_instance._handle_message(invalid_json)

        # Should not call callback for invalid JSON
        mock_callback.assert_not_called()
        
        # Should log error
        mock_logger.error.assert_called_once()
        assert "Error parsing message" in str(mock_logger.error.call_args)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_message_no_callback_set(self, tree_news_instance):
        """Test _handle_message returns early when no callback is set."""
        # Don't set callback
        tree_news_instance._callback = None
        
        sample_message = {"title": "Test", "time": 1640995200000, "suggestions": []}
        message_json = json.dumps(sample_message)
        
        # Should not raise any errors and return early
        await tree_news_instance._handle_message(message_json)
        
        # No assertions needed - just ensuring no exceptions are raised

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_message_empty_suggestions(self, tree_news_instance, mock_callback):
        """Test _handle_message with empty suggestions array."""
        tree_news_instance._callback = mock_callback
        
        message_empty_suggestions = {
            "title": "News without coins",
            "time": 1640995200000,
            "suggestions": []
        }
        
        with patch('app.core.news.tree_news.settings.ENVIRONMENT', 'test'):
            message_json = json.dumps(message_empty_suggestions)
            await tree_news_instance._handle_message(message_json)

        mock_callback.assert_called_once()
        
        call_args = mock_callback.call_args[0]
        news_data = call_args[0]
        
        # Should have empty coins set
        assert news_data.coins == set()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_message_suggestions_without_coin_key(self, tree_news_instance, mock_callback):
        """Test _handle_message with suggestions that don't have 'coin' key."""
        tree_news_instance._callback = mock_callback
        
        message_invalid_suggestions = {
            "title": "News with invalid suggestions",
            "time": 1640995200000,
            "suggestions": [
                {"symbol": "BTC"},  # No 'coin' key
                {"coin": "ETH"},    # Valid
                {"name": "Bitcoin"} # No 'coin' key
            ]
        }
        
        with patch('app.core.news.tree_news.settings.ENVIRONMENT', 'test'):
            message_json = json.dumps(message_invalid_suggestions)
            await tree_news_instance._handle_message(message_json)

        mock_callback.assert_called_once()
        
        call_args = mock_callback.call_args[0]
        news_data = call_args[0]
        
        # Should only include suggestions with 'coin' key
        assert news_data.coins == {"ETH"}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_message_development_environment_logging(self, tree_news_instance, mock_callback, sample_twitter_message):
        """Test _handle_message logs in development environment."""
        tree_news_instance._callback = mock_callback
        
        with patch('app.core.news.tree_news.settings.ENVIRONMENT', 'development'):
            with patch('app.core.news.tree_news.pretty_print') as mock_pretty_print:
                message_json = json.dumps(sample_twitter_message)
                await tree_news_instance._handle_message(message_json)

        # Should call pretty_print in development mode
        mock_pretty_print.assert_called_once_with(sample_twitter_message, ",\n")
        mock_callback.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_message_non_development_environment_no_logging(self, tree_news_instance, mock_callback, sample_twitter_message):
        """Test _handle_message doesn't log in non-development environment."""
        tree_news_instance._callback = mock_callback
        
        with patch('app.core.news.tree_news.settings.ENVIRONMENT', 'production'):
            with patch('app.core.news.tree_news.pretty_print') as mock_pretty_print:
                message_json = json.dumps(sample_twitter_message)
                await tree_news_instance._handle_message(message_json)

        # Should not call pretty_print in production mode
        mock_pretty_print.assert_not_called()
        mock_callback.assert_called_once()
