import pytest
from datetime import datetime, date, time, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.coin import (
    get_trending_coins_by_mentions,
    get_coin_sentiment_divergence_history
)
from app.models.coin import Coin
from app.models.post import Post
from app.models.post_coin import PostCoin


@pytest.mark.unit
class TestCoinService:
    """Test coin service functions with mocked database operations."""

    @pytest.mark.asyncio
    async def test_get_trending_coins_by_mentions_aggregation_logic(self, mock_async_session):
        """Test trending coins aggregation correctly counts mentions and calculates sentiment stats."""
        # Arrange
        today = date.today()
        start_of_day = datetime.combine(today, time.min)
        
        # Mock coins
        btc_coin = Coin(id=1, symbol="BTC", name="Bitcoin", image_url="btc.png")
        eth_coin = Coin(id=2, symbol="ETH", name="Ethereum", image_url="eth.png")
        
        # Mock posts with different sentiments
        posts_btc = [
            Post(id=1, title="BTC bullish", sentiment="Bullish", time=start_of_day + timedelta(hours=1)),
            Post(id=2, title="BTC bearish", sentiment="Bearish", time=start_of_day + timedelta(hours=2)),
            Post(id=3, title="BTC neutral", sentiment="Neutral", time=start_of_day + timedelta(hours=3)),
            Post(id=4, title="BTC bullish again", sentiment="Bullish", time=start_of_day + timedelta(hours=4)),
        ]
        
        posts_eth = [
            Post(id=5, title="ETH bullish", sentiment="Bullish", time=start_of_day + timedelta(hours=1)),
            Post(id=6, title="ETH neutral", sentiment="Neutral", time=start_of_day + timedelta(hours=2)),
        ]
        
        # Create PostCoin relationships
        for post in posts_btc:
            post.post_coins = [PostCoin(coin_id=1, post_id=post.id)]
        for post in posts_eth:
            post.post_coins = [PostCoin(coin_id=2, post_id=post.id)]
        
        # Mock database responses
        mock_results = [
            (btc_coin, 4),  # BTC mentioned 4 times
            (eth_coin, 2),  # ETH mentioned 2 times
        ]
        
        # Setup execute call sequence
        execute_calls = []
        
        # First call: count query
        count_result = MagicMock()
        count_result.scalar_one.return_value = 2
        execute_calls.append(count_result)
        
        # Second call: main query for coins and mention counts
        main_result = MagicMock()
        main_result.all.return_value = mock_results
        execute_calls.append(main_result)
        
        # Third and fourth calls: posts queries for each coin
        btc_posts_result = MagicMock()
        btc_posts_result.unique.return_value.scalars.return_value.all.return_value = posts_btc
        execute_calls.append(btc_posts_result)
        
        eth_posts_result = MagicMock()
        eth_posts_result.unique.return_value.scalars.return_value.all.return_value = posts_eth
        execute_calls.append(eth_posts_result)
        
        mock_async_session.execute = AsyncMock(side_effect=execute_calls)
        
        # Act
        trending_coins, total_count = await get_trending_coins_by_mentions(
            session=mock_async_session,
            page=1,
            page_size=20
        )
        
        # Assert
        assert total_count == 2
        assert len(trending_coins) == 2
        
        # Check BTC (first in results, highest mentions)
        btc_result = trending_coins[0]
        assert btc_result["id"] == 1
        assert btc_result["symbol"] == "BTC"
        assert btc_result["name"] == "Bitcoin"
        assert btc_result["mention_count"] == 4
        assert btc_result["sentiment_stats"]["positive"] == 2  # 2 Bullish posts
        assert btc_result["sentiment_stats"]["negative"] == 1  # 1 Bearish post
        assert btc_result["sentiment_stats"]["neutral"] == 1   # 1 Neutral post
        
        # Check ETH (second in results)
        eth_result = trending_coins[1]
        assert eth_result["id"] == 2
        assert eth_result["symbol"] == "ETH"
        assert eth_result["name"] == "Ethereum"
        assert eth_result["mention_count"] == 2
        assert eth_result["sentiment_stats"]["positive"] == 1  # 1 Bullish post
        assert eth_result["sentiment_stats"]["negative"] == 0  # 0 Bearish posts
        assert eth_result["sentiment_stats"]["neutral"] == 1   # 1 Neutral post
        
        # Verify database was called correct number of times
        assert mock_async_session.execute.call_count == 4

    @pytest.mark.asyncio
    async def test_get_trending_coins_by_mentions_pagination(self, mock_async_session):
        """Test trending coins pagination logic."""
        # Arrange
        coins = [Coin(id=i, symbol=f"COIN{i}", name=f"Coin {i}", image_url=f"coin{i}.png") for i in range(1, 6)]
        mock_results = [(coin, 10 - coin.id) for coin in coins]  # Descending mention counts
        
        # Mock empty posts for simplicity
        empty_posts_result = MagicMock()
        empty_posts_result.unique.return_value.scalars.return_value.all.return_value = []
        
        execute_calls = [
            MagicMock(scalar_one=lambda: 5),  # total count
            MagicMock(all=lambda: mock_results[2:4]),  # page 2, page_size 2
        ]
        # Add empty posts results for each coin
        for _ in mock_results[2:4]:
            execute_calls.append(empty_posts_result)
        
        mock_async_session.execute = AsyncMock(side_effect=execute_calls)
        
        # Act
        trending_coins, total_count = await get_trending_coins_by_mentions(
            session=mock_async_session,
            page=2,
            page_size=2
        )
        
        # Assert
        assert total_count == 5
        assert len(trending_coins) == 2
        assert trending_coins[0]["id"] == 3  # Third coin (page 2, items 3-4)
        assert trending_coins[1]["id"] == 4  # Fourth coin

    @pytest.mark.asyncio
    @patch('app.services.coin.ccxt_async')
    async def test_get_coin_sentiment_divergence_history_daily_grouping(self, mock_ccxt, mock_async_session):
        """Test sentiment divergence history with daily interval grouping."""
        # Mock CCXT to prevent external calls
        mock_binance = AsyncMock()
        mock_ccxt.binance.return_value = mock_binance
        mock_binance.markets = None  # No markets available, will skip CCXT calls
        
        # Arrange
        base_date = datetime(2024, 1, 15, 10, 0, 0)  # Monday
        coin = Coin(id=1, symbol="BTC", name="Bitcoin")
        
        # Create posts across multiple days with different sentiments
        posts = [
            # Day 1: Mixed sentiment (2 Bullish, 1 Bearish) = +1 average
            Post(id=1, sentiment="Bullish", time=base_date, post_coins=[PostCoin(coin_id=1, price_usd=50000)]),
            Post(id=2, sentiment="Bullish", time=base_date + timedelta(hours=2), post_coins=[PostCoin(coin_id=1, price_usd=50100)]),
            Post(id=3, sentiment="Bearish", time=base_date + timedelta(hours=4), post_coins=[PostCoin(coin_id=1, price_usd=49900)]),
            
            # Day 2: All bearish (3 Bearish) = -1 average
            Post(id=4, sentiment="Bearish", time=base_date + timedelta(days=1, hours=1), post_coins=[PostCoin(coin_id=1, price_usd=49000)]),
            Post(id=5, sentiment="Bearish", time=base_date + timedelta(days=1, hours=3), post_coins=[PostCoin(coin_id=1, price_usd=48500)]),
            Post(id=6, sentiment="Bearish", time=base_date + timedelta(days=1, hours=5), post_coins=[PostCoin(coin_id=1, price_usd=48000)]),
            
            # Day 3: All bullish (2 Bullish) = +1 average  
            Post(id=7, sentiment="Bullish", time=base_date + timedelta(days=2, hours=2), post_coins=[PostCoin(coin_id=1, price_usd=52000)]),
            Post(id=8, sentiment="Bullish", time=base_date + timedelta(days=2, hours=6), post_coins=[PostCoin(coin_id=1, price_usd=53000)]),
        ]
        
        # Mock database responses
        coin_result = MagicMock()
        coin_result.scalar_one_or_none.return_value = coin
        
        posts_result = MagicMock()
        posts_result.unique.return_value.scalars.return_value.all.return_value = posts
        
        mock_async_session.execute = AsyncMock(side_effect=[coin_result, posts_result])
        
        # Act
        divergence_data = await get_coin_sentiment_divergence_history(
            session=mock_async_session,
            coin_id="BTC",
            days=7,
            interval="daily"
        )
        
        # Assert
        assert len(divergence_data) == 3  # 3 days of data
        
        # Day 1: 3 mentions, sentiment=+1/3=0.33, price from last post
        day1 = divergence_data[0]
        assert day1["mentions"] == 3
        assert abs(day1["average_sentiment"] - (1/3)) < 0.01  # (1+1-1)/3 = 1/3
        assert day1["price"] == 49900  # Last price from day 1
        assert day1["divergence"] is None  # No previous data to compare
        
        # Day 2: 3 mentions, sentiment=-1, price from last post
        day2 = divergence_data[1]
        assert day2["mentions"] == 3
        assert day2["average_sentiment"] == -1.0  # (-1-1-1)/3 = -1
        assert day2["price"] == 48000  # Last price from day 2
        # No divergence detected (price down, sentiment down - aligned)
        
        # Day 3: 2 mentions, sentiment=+1, price from last post
        day3 = divergence_data[2]
        assert day3["mentions"] == 2
        assert day3["average_sentiment"] == 1.0  # (1+1)/2 = 1
        assert day3["price"] == 53000  # Last price from day 3
        # Potential bullish divergence: price up, sentiment improved

    @pytest.mark.asyncio
    @patch('app.services.coin.ccxt_async')
    async def test_get_coin_sentiment_divergence_history_hourly_grouping(self, mock_ccxt, mock_async_session):
        """Test sentiment divergence history with hourly interval grouping."""
        # Mock CCXT to prevent external calls
        mock_binance = AsyncMock()
        mock_ccxt.binance.return_value = mock_binance
        mock_binance.markets = None  # No markets available, will skip CCXT calls
        
        # Arrange
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        coin = Coin(id=1, symbol="BTC", name="Bitcoin")
        
        # Create posts within same day but different hours
        posts = [
            # Hour 10: 2 Bullish posts
            Post(id=1, sentiment="Bullish", time=base_time + timedelta(minutes=15), post_coins=[PostCoin(coin_id=1, price_usd=50000)]),
            Post(id=2, sentiment="Bullish", time=base_time + timedelta(minutes=45), post_coins=[PostCoin(coin_id=1, price_usd=50100)]),
            
            # Hour 11: 1 Bearish post
            Post(id=3, sentiment="Bearish", time=base_time + timedelta(hours=1, minutes=30), post_coins=[PostCoin(coin_id=1, price_usd=49500)]),
        ]
        
        # Mock database responses
        coin_result = MagicMock()
        coin_result.scalar_one_or_none.return_value = coin
        
        posts_result = MagicMock()
        posts_result.unique.return_value.scalars.return_value.all.return_value = posts
        
        mock_async_session.execute = AsyncMock(side_effect=[coin_result, posts_result])
        
        # Act
        divergence_data = await get_coin_sentiment_divergence_history(
            session=mock_async_session,
            coin_id="BTC",
            days=1,
            interval="hourly"
        )
        
        # Assert
        assert len(divergence_data) == 2  # 2 hours of data
        
        # Hour 1: 2 mentions, sentiment=+1
        hour1 = divergence_data[0]
        assert hour1["mentions"] == 2
        assert hour1["average_sentiment"] == 1.0  # (1+1)/2 = 1
        assert hour1["price"] == 50100  # Last price from hour 10
        
        # Hour 2: 1 mention, sentiment=-1
        hour2 = divergence_data[1]
        assert hour2["mentions"] == 1
        assert hour2["average_sentiment"] == -1.0  # -1/1 = -1
        assert hour2["price"] == 49500  # Price from hour 11

    @pytest.mark.asyncio
    @patch('app.services.coin.ccxt_async')
    async def test_get_coin_sentiment_divergence_history_divergence_detection(self, mock_ccxt, mock_async_session):
        """Test divergence signal detection logic."""
        # Mock CCXT to prevent external calls
        mock_binance = AsyncMock()
        mock_ccxt.binance.return_value = mock_binance
        mock_binance.markets = None  # No markets available, will skip CCXT calls
        
        # Arrange
        base_date = datetime(2024, 1, 15, 0, 0, 0)
        coin = Coin(id=1, symbol="BTC", name="Bitcoin")
        
        # Create scenario for bullish divergence: price down, sentiment up
        posts = [
            # Day 1: Neutral sentiment, high price
            Post(id=1, sentiment="Neutral", time=base_date, post_coins=[PostCoin(coin_id=1, price_usd=55000)]),
            
            # Day 2: Bullish sentiment, lower price (bullish divergence)
            Post(id=2, sentiment="Bullish", time=base_date + timedelta(days=1), post_coins=[PostCoin(coin_id=1, price_usd=50000)]),
            
            # Day 3: High mentions but bearish sentiment (bearish divergence)
            Post(id=3, sentiment="Bearish", time=base_date + timedelta(days=2), post_coins=[PostCoin(coin_id=1, price_usd=51000)]),
            Post(id=4, sentiment="Bearish", time=base_date + timedelta(days=2, hours=2), post_coins=[PostCoin(coin_id=1, price_usd=51000)]),
            Post(id=5, sentiment="Bearish", time=base_date + timedelta(days=2, hours=4), post_coins=[PostCoin(coin_id=1, price_usd=51000)]),
            Post(id=6, sentiment="Bearish", time=base_date + timedelta(days=2, hours=6), post_coins=[PostCoin(coin_id=1, price_usd=51000)]),
        ]
        
        # Mock database responses
        coin_result = MagicMock()
        coin_result.scalar_one_or_none.return_value = coin
        
        posts_result = MagicMock()
        posts_result.unique.return_value.scalars.return_value.all.return_value = posts
        
        mock_async_session.execute = AsyncMock(side_effect=[coin_result, posts_result])
        
        # Act
        divergence_data = await get_coin_sentiment_divergence_history(
            session=mock_async_session,
            coin_id="BTC",
            days=7,
            interval="daily"
        )
        
        # Assert
        assert len(divergence_data) == 3
        
        # Day 1: baseline
        assert divergence_data[0]["divergence"] is None
        
        # Day 2: bullish divergence (price down from 55000 to 50000, sentiment up from 0 to 1)
        assert divergence_data[1]["divergence"] == "bullish"
        assert divergence_data[1]["average_sentiment"] == 1.0
        assert divergence_data[1]["price"] == 50000
        
        # Day 3: bearish divergence (mentions up from 1 to 4, but sentiment down from 1 to -1)
        assert divergence_data[2]["divergence"] == "bearish"
        assert divergence_data[2]["mentions"] == 4
        assert divergence_data[2]["average_sentiment"] == -1.0

    @pytest.mark.asyncio
    @patch('app.services.coin.ccxt_async')
    async def test_get_coin_sentiment_divergence_history_coin_not_found(self, mock_ccxt, mock_async_session):
        """Test sentiment divergence when coin doesn't exist."""
        # Arrange
        coin_result = MagicMock()
        coin_result.scalar_one_or_none.return_value = None
        
        mock_async_session.execute = AsyncMock(return_value=coin_result)
        
        # Act
        divergence_data = await get_coin_sentiment_divergence_history(
            session=mock_async_session,
            coin_id="NONEXISTENT",
            days=7,
            interval="daily"
        )
        
        # Assert
        assert divergence_data == []
        mock_async_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.coin.ccxt_async')
    async def test_get_coin_sentiment_divergence_history_no_posts(self, mock_ccxt, mock_async_session):
        """Test sentiment divergence when coin exists but has no posts."""
        # Mock CCXT to prevent external calls
        mock_binance = AsyncMock()
        mock_ccxt.binance.return_value = mock_binance
        mock_binance.markets = None  # No markets available, will skip CCXT calls
        
        # Arrange
        coin = Coin(id=1, symbol="BTC", name="Bitcoin")
        
        coin_result = MagicMock()
        coin_result.scalar_one_or_none.return_value = coin
        
        posts_result = MagicMock()
        posts_result.unique.return_value.scalars.return_value.all.return_value = []
        
        mock_async_session.execute = AsyncMock(side_effect=[coin_result, posts_result])
        
        # Act
        divergence_data = await get_coin_sentiment_divergence_history(
            session=mock_async_session,
            coin_id="BTC",
            days=7,
            interval="daily"
        )
        
        # Assert
        assert divergence_data == []
        assert mock_async_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_trending_coins_empty_result(self, mock_async_session):
        """Test trending coins when no coins are mentioned today."""
        # Arrange
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        
        main_result = MagicMock()
        main_result.all.return_value = []
        
        mock_async_session.execute = AsyncMock(side_effect=[count_result, main_result])
        
        # Act
        trending_coins, total_count = await get_trending_coins_by_mentions(
            session=mock_async_session,
            page=1,
            page_size=20
        )
        
        # Assert
        assert total_count == 0
        assert trending_coins == []
        assert mock_async_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_trending_coins_sentiment_calculation_edge_cases(self, mock_async_session):
        """Test sentiment calculation with unknown sentiment values."""
        # Arrange
        today = date.today()
        start_of_day = datetime.combine(today, time.min)
        
        coin = Coin(id=1, symbol="BTC", name="Bitcoin", image_url="btc.png")
        
        # Posts with unknown/invalid sentiment values
        posts = [
            Post(id=1, title="BTC post", sentiment="Unknown", time=start_of_day + timedelta(hours=1)),
            Post(id=2, title="BTC post", sentiment="", time=start_of_day + timedelta(hours=2)),
            Post(id=3, title="BTC post", sentiment=None, time=start_of_day + timedelta(hours=3)),
            Post(id=4, title="BTC post", sentiment="Bullish", time=start_of_day + timedelta(hours=4)),
        ]
        
        for post in posts:
            post.post_coins = [PostCoin(coin_id=1, post_id=post.id)]
        
        # Mock database responses
        execute_calls = [
            MagicMock(scalar_one=lambda: 1),  # count
            MagicMock(all=lambda: [(coin, 4)]),  # coins with mentions
            MagicMock(unique=lambda: MagicMock(scalars=lambda: MagicMock(all=lambda: posts)))  # posts
        ]
        
        mock_async_session.execute = AsyncMock(side_effect=execute_calls)
        
        # Act
        trending_coins, total_count = await get_trending_coins_by_mentions(
            session=mock_async_session,
            page=1,
            page_size=20
        )
        
        # Assert
        assert len(trending_coins) == 1
        btc_result = trending_coins[0]
        assert btc_result["sentiment_stats"]["positive"] == 1  # Only 1 Bullish
        assert btc_result["sentiment_stats"]["negative"] == 0  # No Bearish
        assert btc_result["sentiment_stats"]["neutral"] == 0   # No Neutral (unknown sentiments don't count)
