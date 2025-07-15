"""
Integration test specific fixtures and utilities.
"""
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient


@pytest.fixture
def authenticated_client(client: AsyncClient, test_user_token: str):
    """HTTP client with authentication headers."""
    client.headers.update({"Authorization": f"Bearer {test_user_token}"})
    return client


@pytest.fixture
def mock_ccxt_exchange():
    """Mock CCXT exchange for chart data testing."""
    with patch('ccxt.async_support.binance') as mock_exchange:
        mock_instance = AsyncMock()
        mock_instance.fetch_ohlcv = AsyncMock(return_value=[
            [1640995200000, 47000, 48000, 46500, 47500, 1000],
            [1641081600000, 47500, 48500, 47000, 48000, 1200],
        ])
        mock_exchange.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_coingecko_client():
    """Mock CoinGecko client for news integration tests."""
    with patch('app.services.news.coingecko_client') as mock_client:
        mock_client.get_coins_markets = AsyncMock(return_value=[
            {
                "symbol": "btc",
                "name": "Bitcoin",
                "image": "https://example.com/bitcoin.png",
                "current_price": 45000.0
            },
            {
                "symbol": "eth", 
                "name": "Ethereum",
                "image": "https://example.com/ethereum.png",
                "current_price": 3000.0
            }
        ])
        yield mock_client


@pytest.fixture
def mock_cmc_client():
    """Mock CoinMarketCap client for market integration tests."""
    with patch('app.api.routes.rest.market.cmc_client') as mock_client:
        mock_client.get_market_stats = AsyncMock(return_value={
            "data": {
                "quote": {
                    "USD": {
                        "total_market_cap": 1000000000000.0,
                        "total_market_cap_yesterday_percentage_change": 0.0,
                        "total_volume_24h": 50000000000.0,
                        "total_volume_24h_yesterday_percentage_change": 0.0,
                    }
                },
                "btc_dominance": 40.0,
                "eth_dominance": 20.0,
                "btc_dominance_24h_percentage_change": 0.0,
                "eth_dominance_24h_percentage_change": 0.0,
            }
        })
        mock_client.get_fear_greed_index = AsyncMock(return_value={
            "data": {"value": 50}
        })
        yield mock_client


@pytest.fixture
def mock_coingecko_market_client():
    """Mock CoinGecko client for market integration tests."""
    with patch('app.api.routes.rest.market.coingecko_client') as mock_client:
        mock_client.get_coins_markets = AsyncMock(return_value=[
            {
                "id": "bitcoin",
                "symbol": "btc",
                "name": "Bitcoin",
                "image": "https://example.com/bitcoin.png",
                "current_price": 45000.0,
                "market_cap": 900000000000,
                "market_cap_rank": 1,
                "price_change_percentage_24h": 2.5,
                "total_volume": 25000000000
            }
        ])
        yield mock_client


@pytest.fixture
def mock_news_manager():
    """Mock NewsManager for WebSocket tests."""
    with patch('app.api.routes.websocket.news.NewsManager') as mock_manager_class:
        mock_instance = AsyncMock()
        mock_manager_class.get_instance.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_websocket_auth():
    """Mock WebSocket authentication for tests."""
    with patch('app.api.routes.websocket.news.authenticate_ws_connection') as mock_auth:
        yield mock_auth


@pytest.fixture(autouse=True)
def mock_external_services():
    """Auto-use fixture to mock external services for all integration tests."""
    with patch('app.services.news.coingecko_client') as mock_coingecko:
        mock_coingecko.get_coins_markets = AsyncMock(return_value=[])
        yield
