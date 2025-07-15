"""
Unit test specific fixtures and utilities.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.core.news.types import NewsData, DataSource


@pytest.fixture
def mock_sentiment_analyzer():
    """Mock sentiment analyzer."""
    mock = MagicMock()
    mock.analyze_sentiment = MagicMock(return_value=0.65)
    return mock


@pytest.fixture
def mock_news_data():
    """Sample NewsData object for testing."""
    return NewsData(
        title="Test Bitcoin News",
        body="This is a test news item about Bitcoin.",
        url="https://example.com/test-news",
        source=DataSource.TREE_NEWS,
        coin_symbols=["BTC"],
        published_at=datetime.utcnow()
    )


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    mock = MagicMock()
    mock.accept = AsyncMock()
    mock.close = AsyncMock()
    mock.send_text = AsyncMock()
    mock.send_json = AsyncMock()
    return mock


@pytest.fixture
def patch_datetime_now():
    """Patch datetime.utcnow() for consistent testing."""
    fixed_time = datetime(2024, 1, 1, 12, 0, 0)
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = fixed_time
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        yield fixed_time
