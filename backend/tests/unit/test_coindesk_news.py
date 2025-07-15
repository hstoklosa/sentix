import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.core.news.coindesk_news import CoinDeskNews
from app.core.news.types import NewsData, DataSource


class TestCoinDeskNewsProcessArticle:
    """Test the _process_article method of CoinDeskNews class."""

    @pytest.fixture
    def coindesk_instance(self):
        """Create a CoinDeskNews instance for testing."""
        return CoinDeskNews()

    @pytest.fixture
    def mock_callback(self):
        """Mock callback function for CoinDeskNews."""
        return AsyncMock()

    @pytest.fixture
    def sample_coindesk_article(self):
        """Sample CoinDesk article data from API."""
        return {
            "ID": 123456,
            "TITLE": "Bitcoin Price Analysis: Bulls Target $50,000 Mark",
            "BODY": "Bitcoin has been showing strong bullish momentum with institutional adoption increasing. Technical analysis suggests a potential breakout above $50,000 resistance level.",
            "URL": "https://www.coindesk.com/markets/2024/01/15/bitcoin-price-analysis-bulls-target-50000-mark/",
            "IMAGE_URL": "https://www.coindesk.com/resizer/image123.jpg",
            "PUBLISHED_ON": 1640995200,  # Unix timestamp in seconds
            "SOURCE_DATA": {
                "NAME": "CoinDesk Markets",
                "IMAGE_URL": "https://www.coindesk.com/favicon.ico"
            },
            "CATEGORY_DATA": [
                {"NAME": "Bitcoin"},
                {"NAME": "BTC"},
                {"NAME": "Markets"},
                {"NAME": "ETH"},
                {"NAME": "Price Analysis"}
            ]
        }

    @pytest.fixture
    def minimal_coindesk_article(self):
        """Minimal CoinDesk article with required fields only."""
        return {
            "ID": 789012,
            "PUBLISHED_ON": 1640995200
        }

    @pytest.fixture
    def article_with_missing_fields(self):
        """CoinDesk article with some missing optional fields."""
        return {
            "ID": 345678,
            "TITLE": "Ethereum Network Upgrade Complete",
            "URL": "https://www.coindesk.com/tech/ethereum-upgrade-complete/",
            "PUBLISHED_ON": 1640995200,
            "CATEGORY_DATA": [
                {"NAME": "Ethereum"},
                {"NAME": "ETH"},
                {"NAME": "DOGE"}  # Should be included as it's uppercase and ≤ 5 chars
            ]
            # Missing: BODY, IMAGE_URL, SOURCE_DATA
        }

    @pytest.fixture
    def article_with_mixed_categories(self):
        """CoinDesk article with mixed category types."""
        return {
            "ID": 567890,
            "TITLE": "Crypto Market Update",
            "PUBLISHED_ON": 1640995200,
            "CATEGORY_DATA": [
                {"NAME": "BTC"},           # Valid: uppercase, ≤ 5 chars
                {"NAME": "ETH"},           # Valid: uppercase, ≤ 5 chars
                {"NAME": "bitcoin"},       # Invalid: not uppercase
                {"NAME": "ETHEREUM"},      # Invalid: > 5 chars
                {"NAME": "ADA"},           # Valid: uppercase, ≤ 5 chars
                {"NAME": "Price Analysis"}, # Invalid: not uppercase
                {"NAME": "SOL"},           # Valid: uppercase, ≤ 5 chars
                {"NAME": ""},              # Invalid: empty string
                {"NAME": "MATIC"}          # Valid: uppercase, = 5 chars
            ]
        }

    @pytest.fixture
    def article_with_zero_timestamp(self):
        """CoinDesk article with zero timestamp."""
        return {
            "ID": 111111,
            "TITLE": "Test Article",
            "PUBLISHED_ON": 0
        }

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_article_complete_data(self, coindesk_instance, mock_callback, sample_coindesk_article):
        """Test _process_article with complete CoinDesk article data."""
        coindesk_instance._callback = mock_callback
        
        await coindesk_instance._process_article(sample_coindesk_article)

        # Verify callback was called
        mock_callback.assert_called_once()
        
        # Get the NewsData object passed to callback
        call_args = mock_callback.call_args[0]
        news_data = call_args[0]
        
        # Verify NewsData object properties
        assert isinstance(news_data, NewsData)
        assert news_data.feed == "CoinDesk"
        assert news_data.source == "CoinDesk Markets"
        assert news_data.title == "Bitcoin Price Analysis: Bulls Target $50,000 Mark"
        assert news_data.body == sample_coindesk_article["BODY"]
        assert news_data.url == sample_coindesk_article["URL"]
        assert news_data.icon == "https://www.coindesk.com/favicon.ico"
        assert news_data.image == "https://www.coindesk.com/resizer/image123.jpg"
        
        # Verify timestamp conversion (seconds to milliseconds)
        expected_time = datetime.fromtimestamp(1640995200, tz=timezone.utc)
        assert news_data.time == expected_time
        
        # Verify coin symbols extraction (only uppercase, ≤ 5 chars)
        expected_coins = {"BTC", "ETH"}  # "Bitcoin", "Markets", "Price Analysis" should be filtered out
        assert news_data.coins == expected_coins
        
        # Verify Twitter-specific fields are set to False for CoinDesk
        assert news_data.is_reply is False
        assert news_data.is_self_reply is False
        assert news_data.is_quote is False
        assert news_data.is_retweet is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_article_minimal_data(self, coindesk_instance, mock_callback, minimal_coindesk_article):
        """Test _process_article with minimal article data."""
        coindesk_instance._callback = mock_callback
        
        await coindesk_instance._process_article(minimal_coindesk_article)

        mock_callback.assert_called_once()
        
        call_args = mock_callback.call_args[0]
        news_data = call_args[0]
        
        # Verify defaults for missing fields
        assert news_data.feed == "CoinDesk"
        assert news_data.source == "CoinDesk"  # Default when SOURCE_DATA is missing
        assert news_data.title == ""  # Default empty string
        assert news_data.body == ""   # Default empty string
        assert news_data.url == ""    # Default empty string
        assert news_data.icon == ""   # Default empty string
        assert news_data.image == ""  # Default empty string
        assert news_data.coins == set()  # Empty set when no categories
        
        # Verify timestamp is still processed correctly
        expected_time = datetime.fromtimestamp(1640995200, tz=timezone.utc)
        assert news_data.time == expected_time

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_article_missing_fields(self, coindesk_instance, mock_callback, article_with_missing_fields):
        """Test _process_article with some missing optional fields."""
        coindesk_instance._callback = mock_callback
        
        await coindesk_instance._process_article(article_with_missing_fields)

        mock_callback.assert_called_once()
        
        call_args = mock_callback.call_args[0]
        news_data = call_args[0]
        
        # Verify provided fields are correct
        assert news_data.title == "Ethereum Network Upgrade Complete"
        assert news_data.url == "https://www.coindesk.com/tech/ethereum-upgrade-complete/"
        assert news_data.coins == {"ETH", "DOGE"}
        
        # Verify defaults for missing fields
        assert news_data.body == ""
        assert news_data.image == ""
        assert news_data.source == "CoinDesk"  # Default when SOURCE_DATA is missing
        assert news_data.icon == ""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_article_coin_symbol_filtering(self, coindesk_instance, mock_callback, article_with_mixed_categories):
        """Test _process_article correctly filters coin symbols from categories."""
        coindesk_instance._callback = mock_callback
        
        await coindesk_instance._process_article(article_with_mixed_categories)

        mock_callback.assert_called_once()
        
        call_args = mock_callback.call_args[0]
        news_data = call_args[0]
        
        # Should only include uppercase symbols with ≤ 5 characters
        expected_coins = {"BTC", "ETH", "ADA", "SOL", "MATIC"}
        assert news_data.coins == expected_coins

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_article_timestamp_conversion(self, coindesk_instance, mock_callback):
        """Test _process_article correctly converts timestamps from seconds to milliseconds."""
        coindesk_instance._callback = mock_callback
        
        # Test with different timestamp values
        test_cases = [
            {"PUBLISHED_ON": 1640995200, "expected": datetime.fromtimestamp(1640995200, tz=timezone.utc)},
            {"PUBLISHED_ON": 1577836800, "expected": datetime.fromtimestamp(1577836800, tz=timezone.utc)},  # 2020-01-01
            {"PUBLISHED_ON": 0, "expected": datetime.fromtimestamp(0, tz=timezone.utc)},  # Unix epoch
        ]
        
        for i, test_case in enumerate(test_cases):
            article = {
                "ID": i,
                "PUBLISHED_ON": test_case["PUBLISHED_ON"]
            }
            
            await coindesk_instance._process_article(article)
            
            call_args = mock_callback.call_args[0]
            news_data = call_args[0]
            
            assert news_data.time == test_case["expected"]
            mock_callback.reset_mock()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_article_development_environment_logging(self, coindesk_instance, mock_callback, sample_coindesk_article):
        """Test _process_article logs timestamp details in development environment."""
        coindesk_instance._callback = mock_callback
        
        with patch('app.core.news.coindesk_news.settings.ENVIRONMENT', 'development'):
            with patch('app.core.news.coindesk_news.logger') as mock_logger:
                await coindesk_instance._process_article(sample_coindesk_article)

        # Should log debug information in development mode
        mock_logger.debug.assert_called_once()
        log_call = mock_logger.debug.call_args[0][0]
        assert "Raw timestamp:" in log_call
        assert "Converted time:" in log_call
        assert "1640995200" in log_call

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_article_non_development_environment_no_logging(self, coindesk_instance, mock_callback, sample_coindesk_article):
        """Test _process_article doesn't log timestamp details in non-development environment."""
        coindesk_instance._callback = mock_callback
        
        with patch('app.core.news.coindesk_news.settings.ENVIRONMENT', 'production'):
            with patch('app.core.news.coindesk_news.logger') as mock_logger:
                await coindesk_instance._process_article(sample_coindesk_article)

        # Should not call debug logging in production mode
        mock_logger.debug.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_article_no_callback_set(self, coindesk_instance, sample_coindesk_article):
        """Test _process_article returns early when no callback is set."""
        # Don't set callback
        coindesk_instance._callback = None
        
        # Should not raise any errors and return early
        await coindesk_instance._process_article(sample_coindesk_article)
        
        # No assertions needed - just ensuring no exceptions are raised

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_article_empty_category_data(self, coindesk_instance, mock_callback):
        """Test _process_article with empty CATEGORY_DATA."""
        coindesk_instance._callback = mock_callback
        
        article_empty_categories = {
            "ID": 999999,
            "TITLE": "News without categories",
            "PUBLISHED_ON": 1640995200,
            "CATEGORY_DATA": []
        }
        
        await coindesk_instance._process_article(article_empty_categories)

        mock_callback.assert_called_once()
        
        call_args = mock_callback.call_args[0]
        news_data = call_args[0]
        
        # Should have empty coins set
        assert news_data.coins == set()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_article_missing_category_data(self, coindesk_instance, mock_callback):
        """Test _process_article with missing CATEGORY_DATA field."""
        coindesk_instance._callback = mock_callback
        
        article_no_categories = {
            "ID": 888888,
            "TITLE": "News without category data field",
            "PUBLISHED_ON": 1640995200
            # No CATEGORY_DATA field
        }
        
        await coindesk_instance._process_article(article_no_categories)

        mock_callback.assert_called_once()
        
        call_args = mock_callback.call_args[0]
        news_data = call_args[0]
        
        # Should have empty coins set when CATEGORY_DATA is missing
        assert news_data.coins == set()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_article_nested_source_data_missing(self, coindesk_instance, mock_callback):
        """Test _process_article with missing nested SOURCE_DATA fields."""
        coindesk_instance._callback = mock_callback
        
        article_partial_source = {
            "ID": 777777,
            "TITLE": "Test Article",
            "PUBLISHED_ON": 1640995200,
            "SOURCE_DATA": {
                # Missing NAME and IMAGE_URL fields
            }
        }
        
        await coindesk_instance._process_article(article_partial_source)

        mock_callback.assert_called_once()
        
        call_args = mock_callback.call_args[0]
        news_data = call_args[0]
        
        # Should use defaults when nested fields are missing
        assert news_data.source == "CoinDesk"  # Default value
        assert news_data.icon == ""            # Default empty string

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_article_categories_without_name_field(self, coindesk_instance, mock_callback):
        """Test _process_article with categories that don't have 'NAME' field."""
        coindesk_instance._callback = mock_callback
        
        article_invalid_categories = {
            "ID": 666666,
            "TITLE": "News with invalid categories",
            "PUBLISHED_ON": 1640995200,
            "CATEGORY_DATA": [
                {"SYMBOL": "BTC"},  # No 'NAME' field
                {"NAME": "ETH"},    # Valid
                {"ID": 123}         # No 'NAME' field
            ]
        }
        
        await coindesk_instance._process_article(article_invalid_categories)

        mock_callback.assert_called_once()
        
        call_args = mock_callback.call_args[0]
        news_data = call_args[0]
        
        # Should only include categories with 'NAME' field
        assert news_data.coins == {"ETH"}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_article_exception_handling(self, coindesk_instance, mock_callback):
        """Test _process_article handles exceptions gracefully."""
        coindesk_instance._callback = mock_callback
        
        # Create article that will cause an exception during processing
        # Simulate exception by making callback raise an exception
        mock_callback.side_effect = Exception("Test exception")
        
        article = {
            "ID": 555555,
            "TITLE": "Test Article",
            "PUBLISHED_ON": 1640995200
        }
        
        with patch('app.core.news.coindesk_news.logger') as mock_logger:
            await coindesk_instance._process_article(article)

        # Should log error when exception occurs
        mock_logger.error.assert_called_once()
        assert "Error processing CoinDesk article" in str(mock_logger.error.call_args)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_article_edge_case_coin_symbols(self, coindesk_instance, mock_callback):
        """Test _process_article with edge case coin symbols."""
        coindesk_instance._callback = mock_callback
        
        article_edge_cases = {
            "ID": 444444,
            "TITLE": "Edge case symbols",
            "PUBLISHED_ON": 1640995200,
            "CATEGORY_DATA": [
                {"NAME": "A"},        # Valid: 1 char, uppercase
                {"NAME": "ABCDE"},    # Valid: exactly 5 chars, uppercase
                {"NAME": "ABCDEF"},   # Invalid: 6 chars
                {"NAME": "abc"},      # Invalid: lowercase
                {"NAME": "1BTC"},     # Valid: uppercase and ≤ 5 chars
                {"NAME": "BTC1"},     # Valid: uppercase and ≤ 5 chars
                {"NAME": "123"},      # Invalid: numbers don't return True for isupper()
                {"NAME": "B-T"},      # Valid: uppercase and ≤ 5 chars
                {"NAME": "BTC "},     # Valid after strip(): "BTC" is uppercase and ≤ 5 chars
            ]
        }
        
        await coindesk_instance._process_article(article_edge_cases)

        mock_callback.assert_called_once()
        
        call_args = mock_callback.call_args[0]
        news_data = call_args[0]
        
        # Should include all uppercase strings ≤ 5 chars (after strip())
        # The implementation uses: category_name.isupper() and len(category_name) <= 5
        # Note: "123" returns False for isupper() since numbers don't have case
        expected_coins = {"A", "ABCDE", "1BTC", "BTC1", "B-T", "BTC"}
        assert news_data.coins == expected_coins
