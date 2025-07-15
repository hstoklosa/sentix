"""
Integration tests for market endpoints.

These tests validate the market API endpoints by making HTTP requests
and verifying the responses. They use a real test database (in-memory) but 
mock external network calls to CoinMarketCap, CoinGecko, and CCXT.
"""
import pytest
from datetime import datetime, timedelta, timezone, date, time
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient
from sqlmodel import select

from app.models.post import Post
from app.models.coin import Coin
from app.models.post_coin import PostCoin


@pytest.mark.integration
class TestMarketStats:
    """Test market stats endpoint."""

    @pytest.mark.asyncio
    async def test_get_market_stats_success(self, client: AsyncClient, db_session):
        """Test successful retrieval of market stats with sentiment calculation."""
        # Create test posts for today with different sentiments
        today = date.today()
        start_of_day = datetime.combine(today, time.min)
        
        posts = [
            Post(
                title="Bullish Bitcoin News",
                body="Bitcoin is showing strong performance",
                url="https://example.com/bullish1",
                source="TestNews",
                item_type="article",
                feed="Sentix",
                sentiment="Bullish",
                score=0.8,
                time=start_of_day + timedelta(hours=1)
            ),
            Post(
                title="Bearish Market Analysis",
                body="Market concerns are rising",
                url="https://example.com/bearish1",
                source="TestNews",
                item_type="article",
                feed="Sentix",
                sentiment="Bearish",
                score=-0.6,
                time=start_of_day + timedelta(hours=2)
            ),
            Post(
                title="Neutral Market Update",
                body="Market remains stable",
                url="https://example.com/neutral1",
                source="TestNews",
                item_type="article",
                feed="Sentix",
                sentiment="Neutral",
                score=0.1,
                time=start_of_day + timedelta(hours=3)
            ),
            Post(
                title="Another Bullish Signal",
                body="More positive indicators",
                url="https://example.com/bullish2",
                source="TestNews",
                item_type="article",
                feed="Sentix",
                sentiment="Bullish",
                score=0.7,
                time=start_of_day + timedelta(hours=4)
            )
        ]
        
        for post in posts:
            db_session.add(post)
        await db_session.commit()
        
        # Mock CMC client responses
        mock_market_stats = {
            "data": {
                "quote": {
                    "USD": {
                        "total_market_cap": 2000000000000.0,
                        "total_market_cap_yesterday_percentage_change": 2.5,
                        "total_volume_24h": 100000000000.0,
                        "total_volume_24h_yesterday_percentage_change": -1.2,
                    }
                },
                "btc_dominance": 45.5,
                "eth_dominance": 18.2,
                "btc_dominance_24h_percentage_change": 0.8,
                "eth_dominance_24h_percentage_change": -0.3,
            }
        }
        
        mock_fear_greed = {
            "data": {
                "value": 75
            }
        }
        
        with patch('app.api.routes.rest.market.cmc_client') as mock_cmc:
            mock_cmc.get_market_stats = AsyncMock(return_value=mock_market_stats)
            mock_cmc.get_fear_greed_index = AsyncMock(return_value=mock_fear_greed)
            
            response = await client.get("/api/v1/market/")
            
        assert response.status_code == 200
        data = response.json()
        
        # Check market data from CMC
        assert data["total_market_cap"] == 2000000000000.0
        assert data["total_market_cap_24h_change"] == 2.5
        assert data["total_volume_24h"] == 100000000000.0
        assert data["total_volume_24h_change"] == -1.2
        assert data["btc_dominance"] == 45.5
        assert data["eth_dominance"] == 18.2
        assert data["btc_dominance_24h_change"] == 0.8
        assert data["eth_dominance_24h_change"] == -0.3
        assert data["fear_and_greed_index"] == 75
        
        # Check calculated market sentiment
        # 2 Bullish posts, 1 Bearish, 1 Neutral = sentiment_ratio = (2-1)/4 = 0.25 > 0.1 = Bullish
        assert data["market_sentiment"] == "Bullish"

    @pytest.mark.asyncio
    async def test_get_market_stats_bearish_sentiment(self, client: AsyncClient, db_session):
        """Test market stats with bearish sentiment calculation."""
        today = date.today()
        start_of_day = datetime.combine(today, time.min)
        
        # Create posts with more bearish sentiment
        posts = [
            Post(
                title="Bearish Signal 1",
                body="Market decline expected",
                url="https://example.com/bearish1",
                source="TestNews",
                item_type="article",
                feed="Sentix",
                sentiment="Bearish",
                score=-0.8,
                time=start_of_day + timedelta(hours=1)
            ),
            Post(
                title="Bearish Signal 2",
                body="More concerns",
                url="https://example.com/bearish2",
                source="TestNews",
                item_type="article",
                feed="Sentix",
                sentiment="Bearish",
                score=-0.6,
                time=start_of_day + timedelta(hours=2)
            ),
            Post(
                title="Single Bullish Post",
                body="Small positive signal",
                url="https://example.com/bullish1",
                source="TestNews",
                item_type="article",
                feed="Sentix",
                sentiment="Bullish",
                score=0.3,
                time=start_of_day + timedelta(hours=3)
            )
        ]
        
        for post in posts:
            db_session.add(post)
        await db_session.commit()
        
        mock_market_stats = {
            "data": {
                "quote": {"USD": {"total_market_cap": 1000000000000.0}},
                "btc_dominance": 40.0,
                "eth_dominance": 20.0,
                "btc_dominance_24h_percentage_change": 0.0,
                "eth_dominance_24h_percentage_change": 0.0,
            }
        }
        
        with patch('app.api.routes.rest.market.cmc_client') as mock_cmc:
            mock_cmc.get_market_stats = AsyncMock(return_value=mock_market_stats)
            mock_cmc.get_fear_greed_index = AsyncMock(return_value={"data": {"value": 30}})
            
            response = await client.get("/api/v1/market/")
            
        assert response.status_code == 200
        data = response.json()
        
        # sentiment_ratio = (1-2)/3 = -0.33 < -0.1 = Bearish
        assert data["market_sentiment"] == "Bearish"

    @pytest.mark.asyncio
    async def test_get_market_stats_neutral_sentiment(self, client: AsyncClient, db_session):
        """Test market stats with neutral sentiment calculation."""
        today = date.today()
        start_of_day = datetime.combine(today, time.min)
        
        # Create balanced posts
        posts = [
            Post(
                title="Bullish Post",
                body="Some positive news",
                url="https://example.com/bullish1",
                source="TestNews",
                item_type="article",
                feed="Sentix",
                sentiment="Bullish",
                score=0.5,
                time=start_of_day + timedelta(hours=1)
            ),
            Post(
                title="Bearish Post",
                body="Some negative news",
                url="https://example.com/bearish1",
                source="TestNews",
                item_type="article",
                feed="Sentix",
                sentiment="Bearish",
                score=-0.5,
                time=start_of_day + timedelta(hours=2)
            ),
            Post(
                title="Neutral Post",
                body="Market update",
                url="https://example.com/neutral1",
                source="TestNews",
                item_type="article",
                feed="Sentix",
                sentiment="Neutral",
                score=0.0,
                time=start_of_day + timedelta(hours=3)
            )
        ]
        
        for post in posts:
            db_session.add(post)
        await db_session.commit()
        
        mock_market_stats = {
            "data": {
                "quote": {"USD": {"total_market_cap": 1500000000000.0}},
                "btc_dominance": 42.5,
                "eth_dominance": 19.0,
                "btc_dominance_24h_percentage_change": 0.0,
                "eth_dominance_24h_percentage_change": 0.0,
            }
        }
        
        with patch('app.api.routes.rest.market.cmc_client') as mock_cmc:
            mock_cmc.get_market_stats = AsyncMock(return_value=mock_market_stats)
            mock_cmc.get_fear_greed_index = AsyncMock(return_value={"data": {"value": 50}})
            
            response = await client.get("/api/v1/market/")
            
        assert response.status_code == 200
        data = response.json()
        
        # sentiment_ratio = (1-1)/3 = 0 (within -0.1 to 0.1 range) = Neutral
        assert data["market_sentiment"] == "Neutral"

    @pytest.mark.asyncio
    async def test_get_market_stats_no_posts_today(self, client: AsyncClient, db_session):
        """Test market stats when there are no posts today."""
        # Create posts from yesterday
        yesterday = date.today() - timedelta(days=1)
        start_of_yesterday = datetime.combine(yesterday, time.min)
        
        post = Post(
            title="Yesterday's News",
            body="Old news",
            url="https://example.com/old",
            source="TestNews",
            item_type="article",
            feed="Sentix",
            sentiment="Bullish",
            score=0.8,
            time=start_of_yesterday + timedelta(hours=1)
        )
        
        db_session.add(post)
        await db_session.commit()
        
        mock_market_stats = {
            "data": {
                "quote": {"USD": {"total_market_cap": 1000000000000.0}},
                "btc_dominance": 40.0,
                "eth_dominance": 20.0,
                "btc_dominance_24h_percentage_change": 0.0,
                "eth_dominance_24h_percentage_change": 0.0,
            }
        }
        
        with patch('app.api.routes.rest.market.cmc_client') as mock_cmc:
            mock_cmc.get_market_stats = AsyncMock(return_value=mock_market_stats)
            mock_cmc.get_fear_greed_index = AsyncMock(return_value={"data": {"value": 50}})
            
            response = await client.get("/api/v1/market/")
            
        assert response.status_code == 200
        data = response.json()
        
        # No posts today = Neutral sentiment
        assert data["market_sentiment"] == "Neutral"

    @pytest.mark.asyncio
    async def test_get_market_stats_with_force_refresh(self, client: AsyncClient):
        """Test market stats endpoint with force_refresh parameter."""
        mock_market_stats = {
            "data": {
                "quote": {"USD": {"total_market_cap": 1000000000000.0}},
                "btc_dominance": 40.0,
                "eth_dominance": 20.0,
                "btc_dominance_24h_percentage_change": 0.0,
                "eth_dominance_24h_percentage_change": 0.0,
            }
        }
        
        with patch('app.api.routes.rest.market.cmc_client') as mock_cmc:
            mock_cmc.get_market_stats = AsyncMock(return_value=mock_market_stats)
            mock_cmc.get_fear_greed_index = AsyncMock(return_value={"data": {"value": 50}})
            
            response = await client.get("/api/v1/market/?force_refresh=true")
            
            # Verify force_refresh was passed to the client
            mock_cmc.get_market_stats.assert_called_once_with(force_refresh=True)
            mock_cmc.get_fear_greed_index.assert_called_once_with(force_refresh=True)
            
        assert response.status_code == 200


@pytest.mark.integration
class TestCoinsList:
    """Test coins list endpoint."""

    @pytest.mark.asyncio
    async def test_get_coins_success(self, client: AsyncClient):
        """Test successful retrieval of coins list."""
        mock_coins_data = [
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
            },
            {
                "id": "ethereum",
                "symbol": "eth",
                "name": "Ethereum",
                "image": "https://example.com/ethereum.png",
                "current_price": 3000.0,
                "market_cap": 350000000000,
                "market_cap_rank": 2,
                "price_change_percentage_24h": -1.2,
                "total_volume": 15000000000
            }
        ]
        
        with patch('app.api.routes.rest.market.coingecko_client') as mock_coingecko:
            mock_coingecko.get_coins_markets = AsyncMock(return_value=mock_coins_data)
            
            response = await client.get("/api/v1/market/coins")
            
        assert response.status_code == 200
        data = response.json()
        
        # Check pagination structure
        assert "page" in data
        assert "page_size" in data
        assert "total" in data
        assert "total_pages" in data
        assert "has_next" in data
        assert "has_prev" in data
        assert "items" in data
        
        # Check pagination values
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["has_prev"] is False
        
        # Check coin data
        items = data["items"]
        assert len(items) == 2
        
        bitcoin = items[0]
        assert bitcoin["id"] == "bitcoin"
        assert bitcoin["symbol"] == "btc"
        assert bitcoin["name"] == "Bitcoin"
        assert bitcoin["image"] == "https://example.com/bitcoin.png"
        assert bitcoin["current_price"] == 45000.0
        assert bitcoin["market_cap"] == 900000000000
        assert bitcoin["market_cap_rank"] == 1
        assert bitcoin["price_change_percentage_24h"] == 2.5
        assert bitcoin["volume_24h"] == 25000000000
        
        ethereum = items[1]
        assert ethereum["id"] == "ethereum"
        assert ethereum["symbol"] == "eth"
        assert ethereum["name"] == "Ethereum"

    @pytest.mark.asyncio
    async def test_get_coins_with_pagination(self, client: AsyncClient):
        """Test coins list with pagination parameters."""
        mock_coins_data = [{"id": f"coin{i}", "symbol": f"c{i}", "name": f"Coin {i}"} for i in range(10)]
        
        with patch('app.api.routes.rest.market.coingecko_client') as mock_coingecko:
            mock_coingecko.get_coins_markets = AsyncMock(return_value=mock_coins_data)
            
            response = await client.get("/api/v1/market/coins?page=2&page_size=5")
            
            # Verify pagination was passed to the client
            mock_coingecko.get_coins_markets.assert_called_once_with(
                page=2, 
                limit=5, 
                force_refresh=False
            )
            
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 2
        assert data["page_size"] == 5

    @pytest.mark.asyncio
    async def test_get_coins_with_force_refresh(self, client: AsyncClient):
        """Test coins list with force_refresh parameter."""
        with patch('app.api.routes.rest.market.coingecko_client') as mock_coingecko:
            mock_coingecko.get_coins_markets = AsyncMock(return_value=[])
            
            response = await client.get("/api/v1/market/coins?force_refresh=true")
            
            mock_coingecko.get_coins_markets.assert_called_once_with(
                page=1, 
                limit=20, 
                force_refresh=True
            )
            
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_coins_empty_response(self, client: AsyncClient):
        """Test coins list with empty response from CoinGecko."""
        with patch('app.api.routes.rest.market.coingecko_client') as mock_coingecko:
            mock_coingecko.get_coins_markets = AsyncMock(return_value=[])
            
            response = await client.get("/api/v1/market/coins")
            
        assert response.status_code == 200
        data = response.json()
        
        assert data["items"] == []
        assert data["page"] == 1
        assert data["total"] >= 0  # Should be at least 0


@pytest.mark.integration
class TestCoinChartData:
    """Test coin chart data endpoint."""

    @pytest.mark.asyncio
    async def test_get_coin_chart_data_success(self, client: AsyncClient):
        """Test successful retrieval of coin chart data."""
        mock_ohlcv_data = [
            [1640995200000, 47000.0, 48000.0, 46500.0, 47500.0, 1000.0],
            [1641081600000, 47500.0, 48500.0, 47000.0, 48000.0, 1200.0],
            [1641168000000, 48000.0, 49000.0, 47800.0, 48800.0, 1100.0],
        ]
        
        with patch('ccxt.async_support.binance') as mock_binance_class:
            mock_exchange = AsyncMock()
            mock_exchange.load_markets = AsyncMock()
            mock_exchange.markets = {"BTC/USDT": {}}
            mock_exchange.fetch_ohlcv = AsyncMock(return_value=mock_ohlcv_data)
            mock_exchange.close = AsyncMock()
            mock_exchange.milliseconds = MagicMock(return_value=1640995200000)  # Regular MagicMock for synchronous method
            mock_binance_class.return_value = mock_exchange
            
            response = await client.get("/api/v1/market/coins/btc/chart")
            
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "prices" in data
        assert "market_caps" in data
        assert "volumes" in data
        
        # Check prices data
        prices = data["prices"]
        assert len(prices) == 3
        
        assert prices[0]["timestamp"] == 1640995200000
        assert prices[0]["value"] == 47500.0
        assert prices[1]["timestamp"] == 1641081600000
        assert prices[1]["value"] == 48000.0
        assert prices[2]["timestamp"] == 1641168000000
        assert prices[2]["value"] == 48800.0
        
        # Check volumes data
        volumes = data["volumes"]
        assert len(volumes) == 3
        assert volumes[0]["value"] == 1000.0
        assert volumes[1]["value"] == 1200.0
        assert volumes[2]["value"] == 1100.0
        
        # Market caps should be empty (CCXT doesn't provide this)
        assert data["market_caps"] == []

    @pytest.mark.asyncio
    async def test_get_coin_chart_data_with_params(self, client: AsyncClient):
        """Test chart data with different parameters."""
        with patch('ccxt.async_support.binance') as mock_binance_class:
            mock_exchange = AsyncMock()
            mock_exchange.load_markets = AsyncMock()
            mock_exchange.markets = {"ETH/USDT": {}}
            mock_exchange.fetch_ohlcv = AsyncMock(return_value=[])
            mock_exchange.close = AsyncMock()
            mock_exchange.milliseconds = MagicMock(return_value=1640995200000)  # Regular MagicMock for synchronous method
            mock_binance_class.return_value = mock_exchange
            
            response = await client.get("/api/v1/market/coins/eth/chart?days=7&interval=hourly")
            
            # Verify correct parameters were passed
            mock_exchange.fetch_ohlcv.assert_called_once_with(
                "ETH/USDT", 
                timeframe="1h", 
                since=mock_exchange.milliseconds() - 7 * 24 * 60 * 60 * 1000,
                limit=7 * 24
            )
            
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_coin_chart_data_max_days(self, client: AsyncClient):
        """Test chart data with max days parameter."""
        with patch('ccxt.async_support.binance') as mock_binance_class:
            mock_exchange = AsyncMock()
            mock_exchange.load_markets = AsyncMock()
            mock_exchange.markets = {"BTC/USDT": {}}
            mock_exchange.fetch_ohlcv = AsyncMock(return_value=[])
            mock_exchange.close = AsyncMock()
            mock_binance_class.return_value = mock_exchange
            
            response = await client.get("/api/v1/market/coins/btc/chart?days=max")
            
            # Verify max parameters were passed
            mock_exchange.fetch_ohlcv.assert_called_once_with(
                "BTC/USDT", 
                timeframe="1d", 
                since=None,
                limit=None
            )
            
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_coin_chart_data_invalid_pair(self, client: AsyncClient):
        """Test chart data for non-existent trading pair."""
        with patch('ccxt.async_support.binance') as mock_binance_class:
            mock_exchange = AsyncMock()
            mock_exchange.load_markets = AsyncMock()
            mock_exchange.markets = {}  # Empty markets (pair not found)
            mock_exchange.close = AsyncMock()
            mock_binance_class.return_value = mock_exchange
            
            response = await client.get("/api/v1/market/coins/invalidcoin/chart")
            
        # The current implementation catches the HTTPException and returns 502
        # This is actually a bug in the implementation, but we test current behavior
        assert response.status_code == 502
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_coin_chart_data_ccxt_error(self, client: AsyncClient):
        """Test chart data when CCXT raises an error."""
        with patch('ccxt.async_support.binance') as mock_binance_class:
            mock_exchange = AsyncMock()
            mock_exchange.load_markets = AsyncMock(side_effect=Exception("Network error"))
            mock_exchange.close = AsyncMock()
            mock_binance_class.return_value = mock_exchange
            
            response = await client.get("/api/v1/market/coins/btc/chart")
            
        assert response.status_code == 502
        data = response.json()
        assert "Failed to fetch chart data" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_coin_chart_data_invalid_params(self, client: AsyncClient):
        """Test chart data with invalid parameters - should use defaults."""
        with patch('ccxt.async_support.binance') as mock_binance_class:
            mock_exchange = AsyncMock()
            mock_exchange.load_markets = AsyncMock()
            mock_exchange.markets = {"BTC/USDT": {}}
            mock_exchange.fetch_ohlcv = AsyncMock(return_value=[])
            mock_exchange.close = AsyncMock()
            mock_exchange.milliseconds = MagicMock(return_value=1640995200000)  # Regular MagicMock for synchronous method
            mock_binance_class.return_value = mock_exchange
            
            # Invalid interval and days should fall back to defaults
            response = await client.get("/api/v1/market/coins/btc/chart?days=999&interval=invalid")
            
            # Should use default values: days=30, interval=daily
            mock_exchange.fetch_ohlcv.assert_called_once_with(
                "BTC/USDT", 
                timeframe="1d", 
                since=mock_exchange.milliseconds() - 30 * 24 * 60 * 60 * 1000,
                limit=30
            )
            
        assert response.status_code == 200


@pytest.mark.integration
class TestCoinSentimentDivergence:
    """Test coin sentiment divergence endpoint."""

    @pytest.mark.asyncio
    async def test_get_sentiment_divergence_success(self, client: AsyncClient, db_session):
        """Test successful retrieval of sentiment divergence data."""
        # Create test coin
        coin = Coin(
            symbol="BTC",
            name="Bitcoin",
            coingecko_id="bitcoin"
        )
        db_session.add(coin)
        await db_session.commit()
        await db_session.refresh(coin)
        
        # Create test posts with varying sentiment over time
        base_time = datetime.now(timezone.utc) - timedelta(days=5)
        
        posts_data = [
            # Day 1: Bullish sentiment
            {"sentiment": "Bullish", "time": base_time},
            {"sentiment": "Bullish", "time": base_time + timedelta(hours=2)},
            # Day 2: Mixed sentiment
            {"sentiment": "Bearish", "time": base_time + timedelta(days=1)},
            {"sentiment": "Neutral", "time": base_time + timedelta(days=1, hours=3)},
            # Day 3: Bearish sentiment
            {"sentiment": "Bearish", "time": base_time + timedelta(days=2)},
            {"sentiment": "Bearish", "time": base_time + timedelta(days=2, hours=1)},
        ]
        
        posts = []
        for i, post_data in enumerate(posts_data):
            post = Post(
                title=f"Bitcoin News {i+1}",
                body=f"Bitcoin analysis {i+1}",
                url=f"https://example.com/btc-{i+1}",
                source="TestNews",
                item_type="article",
                feed="Sentix",
                sentiment=post_data["sentiment"],
                score=0.5,
                time=post_data["time"]
            )
            db_session.add(post)
            posts.append(post)
            
        await db_session.commit()
        
        # Create PostCoin relationships
        for post in posts:
            await db_session.refresh(post)
            post_coin = PostCoin(post_id=post.id, coin_id=coin.id)
            db_session.add(post_coin)
            
        await db_session.commit()
        
        # Mock CCXT price data
        mock_ohlcv_data = [
            [int((base_time).timestamp() * 1000), 45000.0, 46000.0, 44000.0, 45500.0, 1000.0],
            [int((base_time + timedelta(days=1)).timestamp() * 1000), 45500.0, 47000.0, 45000.0, 46000.0, 1100.0],
            [int((base_time + timedelta(days=2)).timestamp() * 1000), 46000.0, 46500.0, 44500.0, 44800.0, 1200.0],
        ]
        
        with patch('ccxt.async_support.binance') as mock_binance_class:
            mock_exchange = AsyncMock()
            mock_exchange.load_markets = AsyncMock()
            mock_exchange.markets = {"BTC/USDT": {}}
            mock_exchange.fetch_ohlcv = AsyncMock(return_value=mock_ohlcv_data)
            mock_exchange.close = AsyncMock()
            mock_binance_class.return_value = mock_exchange
            
            response = await client.get("/api/v1/market/coins/btc/sentiment-divergence")
            
        assert response.status_code == 200
        data = response.json()
        
        # Should return a list of divergence data points
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check structure of data points
        for point in data:
            assert "timestamp" in point
            assert "average_sentiment" in point
            assert "mentions" in point
            assert "price" in point
            assert "divergence" in point

    @pytest.mark.asyncio
    async def test_get_sentiment_divergence_with_params(self, client: AsyncClient, db_session):
        """Test sentiment divergence with different parameters."""
        # Create test coin
        coin = Coin(
            symbol="ETH",
            name="Ethereum",
            coingecko_id="ethereum"
        )
        db_session.add(coin)
        await db_session.commit()
        await db_session.refresh(coin)
        
        # Create minimal test data
        post = Post(
            title="Ethereum News",
            body="Ethereum analysis",
            url="https://example.com/eth-1",
            source="TestNews",
            item_type="article",
            feed="Sentix",
            sentiment="Bullish",
            score=0.8,
            time=datetime.now(timezone.utc) - timedelta(hours=2)
        )
        db_session.add(post)
        await db_session.commit()
        await db_session.refresh(post)
        
        post_coin = PostCoin(post_id=post.id, coin_id=coin.id)
        db_session.add(post_coin)
        await db_session.commit()
        
        with patch('ccxt.async_support.binance') as mock_binance_class:
            mock_exchange = AsyncMock()
            mock_exchange.load_markets = AsyncMock()
            mock_exchange.markets = {"ETH/USDT": {}}
            mock_exchange.fetch_ohlcv = AsyncMock(return_value=[])
            mock_exchange.close = AsyncMock()
            mock_binance_class.return_value = mock_exchange
            
            response = await client.get("/api/v1/market/coins/eth/sentiment-divergence?days=7&interval=hourly")
            
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_sentiment_divergence_invalid_coin(self, client: AsyncClient):
        """Test sentiment divergence for non-existent coin."""
        response = await client.get("/api/v1/market/coins/nonexistent/sentiment-divergence")
        
        assert response.status_code == 200
        data = response.json()
        assert data == []  # Should return empty list for non-existent coin

    @pytest.mark.asyncio
    async def test_get_sentiment_divergence_invalid_params(self, client: AsyncClient, db_session):
        """Test sentiment divergence with invalid parameters - should use defaults."""
        # Create test coin
        coin = Coin(
            symbol="ADA",
            name="Cardano",
            coingecko_id="cardano"
        )
        db_session.add(coin)
        await db_session.commit()
        
        with patch('ccxt.async_support.binance') as mock_binance_class:
            mock_exchange = AsyncMock()
            mock_exchange.load_markets = AsyncMock()
            mock_exchange.markets = {"ADA/USDT": {}}
            mock_exchange.fetch_ohlcv = AsyncMock(return_value=[])
            mock_exchange.close = AsyncMock()
            mock_binance_class.return_value = mock_exchange
            
            # Invalid params should fall back to defaults
            response = await client.get("/api/v1/market/coins/ada/sentiment-divergence?days=999&interval=invalid")
            
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_sentiment_divergence_max_days(self, client: AsyncClient, db_session):
        """Test sentiment divergence with max days parameter."""
        coin = Coin(
            symbol="BTC",
            name="Bitcoin",
            coingecko_id="bitcoin"
        )
        db_session.add(coin)
        await db_session.commit()
        
        with patch('ccxt.async_support.binance') as mock_binance_class:
            mock_exchange = AsyncMock()
            mock_exchange.load_markets = AsyncMock()
            mock_exchange.markets = {"BTC/USDT": {}}
            mock_exchange.fetch_ohlcv = AsyncMock(return_value=[])
            mock_exchange.close = AsyncMock()
            mock_binance_class.return_value = mock_exchange
            
            response = await client.get("/api/v1/market/coins/btc/sentiment-divergence?days=max")
            
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_sentiment_divergence_ccxt_error(self, client: AsyncClient, db_session):
        """Test sentiment divergence when CCXT fails - should still return data."""
        coin = Coin(
            symbol="BTC",
            name="Bitcoin",
            coingecko_id="bitcoin"
        )
        db_session.add(coin)
        await db_session.commit()
        await db_session.refresh(coin)
        
        # Create test post
        post = Post(
            title="Bitcoin News",
            body="Bitcoin analysis",
            url="https://example.com/btc-1",
            source="TestNews",
            item_type="article",
            feed="Sentix",
            sentiment="Bullish",
            score=0.8,
            time=datetime.now(timezone.utc) - timedelta(hours=2)
        )
        db_session.add(post)
        await db_session.commit()
        await db_session.refresh(post)
        
        post_coin = PostCoin(post_id=post.id, coin_id=coin.id)
        db_session.add(post_coin)
        await db_session.commit()
        
        with patch('ccxt.async_support.binance') as mock_binance_class:
            mock_exchange = AsyncMock()
            mock_exchange.load_markets = AsyncMock(side_effect=Exception("Network error"))
            mock_exchange.close = AsyncMock()
            mock_binance_class.return_value = mock_exchange
            
            response = await client.get("/api/v1/market/coins/btc/sentiment-divergence")
            
        # Should still return data even if CCXT fails
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
