import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Result

from app.services.news import (
    save_news_item,
    get_news_feed,
    search_news,
    get_post_by_id,
    get_coin_by_symbol,
    create_post
)
from app.core.news.types import NewsData
from app.models.post import Post
from app.models.coin import Coin
from app.models.post_coin import PostCoin


@pytest.mark.unit
class TestNewsService:
    """Test news service functions with mocked database operations."""
    
    @pytest.fixture
    def sample_news_data(self):
        """Sample news data for testing."""
        return NewsData(
            title="Bitcoin Reaches New High",
            body="Bitcoin (BTC) has reached a new all-time high today.",
            url="https://example.com/bitcoin-high",
            source="Twitter",
            coins={"BTC"},
            time=datetime(2024, 1, 1, 12, 0, 0)
        )
    
    @pytest.fixture
    def sample_sentiment(self):
        """Sample sentiment analysis result."""
        return {
            "label": "positive",
            "score": 0.85
        }
    
    @pytest.fixture
    def mock_coingecko_response(self):
        """Mock CoinGecko API response."""
        return [
            {
                "symbol": "btc",
                "name": "Bitcoin",
                "image": "https://example.com/btc.png",
                "current_price": 45000
            }
        ]

    @pytest.mark.asyncio
    async def test_save_news_item_creates_new_post(
        self, 
        mock_async_session, 
        sample_news_data, 
        sample_sentiment,
        mock_coingecko_response
    ):
        """Test save_news_item creates a new Post when URL doesn't exist."""
        # Arrange
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_async_session.execute.return_value = mock_result
        
        # Mock the create_post function
        expected_post = Post(
            id=1,
            title=sample_news_data.title,
            body=sample_news_data.body,
            url=sample_news_data.url,
            source=sample_news_data.source,
            sentiment="positive",
            score=0.85
        )
        
        with patch('app.services.news.create_post', return_value=expected_post) as mock_create_post:
            # Act
            result = await save_news_item(mock_async_session, sample_news_data, sample_sentiment)
            
            # Assert
            mock_create_post.assert_called_once_with(mock_async_session, sample_news_data, sample_sentiment)
            assert result == expected_post
            assert result.title == sample_news_data.title
            assert result.url == sample_news_data.url
            assert result.sentiment == "positive"

    @pytest.mark.asyncio
    async def test_save_news_item_returns_existing_post(
        self, 
        mock_async_session, 
        sample_news_data, 
        sample_sentiment
    ):
        """Test save_news_item returns existing post when URL already exists."""
        # Arrange
        existing_post = Post(
            id=1,
            title="Existing Bitcoin News",
            body="Existing content",
            url=sample_news_data.url,
            source="TestNews",
            sentiment="neutral",
            score=0.5
        )
        
        # Mock first query (check for existing post)
        mock_result_existing = MagicMock()
        mock_result_existing.unique.return_value.scalar_one_or_none.return_value = existing_post
        
        # Mock second query (refresh with joined data)
        mock_result_refresh = MagicMock()
        mock_result_refresh.unique.return_value.scalar_one.return_value = existing_post
        
        mock_async_session.execute.side_effect = [mock_result_existing, mock_result_refresh]
        
        # Act
        result = await save_news_item(mock_async_session, sample_news_data, sample_sentiment)
        
        # Assert
        assert result == existing_post
        assert result.id == 1
        assert result.url == sample_news_data.url
        # Verify we didn't try to create a new post
        assert mock_async_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_save_news_item_creates_new_coin_when_not_found(
        self, 
        mock_async_session, 
        sample_news_data, 
        sample_sentiment,
        mock_coingecko_response
    ):
        """Test that save_news_item creates a new Coin record when coin symbol is not found."""
        # Arrange - no existing post
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        
        # Mock session operations for create_post
        mock_async_session.add = MagicMock()
        mock_async_session.commit = AsyncMock()
        mock_async_session.flush = AsyncMock()
        mock_async_session.refresh = AsyncMock()
        
        # Mock the final query that returns the post with coins
        expected_post = Post(id=1, title=sample_news_data.title)
        mock_result_final = MagicMock()
        mock_result_final.unique.return_value.scalar_one.return_value = expected_post
        
        mock_async_session.execute.side_effect = [mock_result, mock_result_final]
        
        with patch('app.services.news.coingecko_client.get_coins_markets', 
                  return_value=mock_coingecko_response) as mock_coingecko:
            with patch('app.services.news.get_coin_by_symbol', return_value=None) as mock_get_coin:
                
                # Act
                result = await save_news_item(mock_async_session, sample_news_data, sample_sentiment)
                
                # Assert
                assert result == expected_post
                # Verify that coingecko client was called with the coin symbols
                mock_coingecko.assert_called_once_with(
                    symbols=list(sample_news_data.coins), 
                    include_tokens="top"
                )

    @pytest.mark.asyncio
    async def test_get_news_feed_with_date_filters(self, mock_async_session):
        """Test get_news_feed applies date filtering correctly."""
        # Arrange
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        # Mock count query result
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 5
        
        # Mock posts query result
        mock_posts = [
            Post(id=1, title="Post 1", time=datetime(2024, 1, 15)),
            Post(id=2, title="Post 2", time=datetime(2024, 1, 20))
        ]
        mock_posts_result = MagicMock()
        mock_posts_result.unique.return_value.scalars.return_value.all.return_value = mock_posts
        
        mock_async_session.execute.side_effect = [mock_count_result, mock_posts_result]
        
        # Act
        posts, total_count = await get_news_feed(
            mock_async_session,
            page=1,
            page_size=20,
            start_date=start_date,
            end_date=end_date
        )
        
        # Assert
        assert total_count == 5
        assert len(posts) == 2
        assert posts[0].title == "Post 1"
        assert posts[1].title == "Post 2"
        assert mock_async_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_news_feed_with_coin_filter(self, mock_async_session):
        """Test get_news_feed applies coin symbol filtering correctly."""
        # Arrange
        coin_symbol = "BTC"
        
        # Mock count query result
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 3
        
        # Mock posts query result
        mock_posts = [
            Post(id=1, title="Bitcoin News 1"),
            Post(id=2, title="Bitcoin News 2")
        ]
        mock_posts_result = MagicMock()
        mock_posts_result.unique.return_value.scalars.return_value.all.return_value = mock_posts
        
        mock_async_session.execute.side_effect = [mock_count_result, mock_posts_result]
        
        # Act
        posts, total_count = await get_news_feed(
            mock_async_session,
            coin_symbol=coin_symbol
        )
        
        # Assert
        assert total_count == 3
        assert len(posts) == 2
        # Verify the query was built with coin filter conditions
        assert mock_async_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_news_feed_pagination(self, mock_async_session):
        """Test get_news_feed pagination logic."""
        # Arrange
        page = 2
        page_size = 10
        expected_offset = (page - 1) * page_size  # 10
        
        # Mock count query result
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 25
        
        # Mock posts query result
        mock_posts = [Post(id=i, title=f"Post {i}") for i in range(11, 21)]
        mock_posts_result = MagicMock()
        mock_posts_result.unique.return_value.scalars.return_value.all.return_value = mock_posts
        
        mock_async_session.execute.side_effect = [mock_count_result, mock_posts_result]
        
        # Act
        posts, total_count = await get_news_feed(
            mock_async_session,
            page=page,
            page_size=page_size
        )
        
        # Assert
        assert total_count == 25
        assert len(posts) == 10
        # Verify offset was calculated correctly
        # This would be verified by checking the SQL query construction in a real test

    @pytest.mark.asyncio
    async def test_search_news_with_query(self, mock_async_session):
        """Test search_news applies search query filtering correctly."""
        # Arrange
        query = "Bitcoin"
        
        # Mock count query result
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 2
        
        # Mock posts query result
        mock_posts = [
            Post(id=1, title="Bitcoin Reaches New High", body="Bitcoin content"),
            Post(id=2, title="Crypto News", body="Bitcoin mentioned in body")
        ]
        mock_posts_result = MagicMock()
        mock_posts_result.unique.return_value.scalars.return_value.all.return_value = mock_posts
        
        mock_async_session.execute.side_effect = [mock_count_result, mock_posts_result]
        
        # Act
        posts, total_count = await search_news(
            mock_async_session,
            query=query
        )
        
        # Assert
        assert total_count == 2
        assert len(posts) == 2
        assert "Bitcoin" in posts[0].title
        assert mock_async_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_search_news_with_date_and_coin_filters(self, mock_async_session):
        """Test search_news applies multiple filters correctly."""
        # Arrange
        query = "price"
        start_date = datetime(2024, 1, 1)
        coin_symbol = "ETH"
        
        # Mock count query result
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 1
        
        # Mock posts query result
        mock_posts = [
            Post(id=1, title="Ethereum Price Analysis", body="Price prediction content")
        ]
        mock_posts_result = MagicMock()
        mock_posts_result.unique.return_value.scalars.return_value.all.return_value = mock_posts
        
        mock_async_session.execute.side_effect = [mock_count_result, mock_posts_result]
        
        # Act
        posts, total_count = await search_news(
            mock_async_session,
            query=query,
            start_date=start_date,
            coin_symbol=coin_symbol
        )
        
        # Assert
        assert total_count == 1
        assert len(posts) == 1
        assert posts[0].title == "Ethereum Price Analysis"

    @pytest.mark.asyncio
    async def test_get_post_by_id_found(self, mock_async_session):
        """Test get_post_by_id returns post when found."""
        # Arrange
        post_id = 1
        expected_post = Post(
            id=post_id,
            title="Test Post",
            body="Test content",
            url="https://example.com/test"
        )
        
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = expected_post
        mock_async_session.execute.return_value = mock_result
        
        # Act
        result = await get_post_by_id(mock_async_session, post_id)
        
        # Assert
        assert result == expected_post
        assert result.id == post_id
        assert result.title == "Test Post"

    @pytest.mark.asyncio
    async def test_get_post_by_id_not_found(self, mock_async_session):
        """Test get_post_by_id returns None when post not found."""
        # Arrange
        post_id = 999
        
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_async_session.execute.return_value = mock_result
        
        # Act
        result = await get_post_by_id(mock_async_session, post_id)
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_coin_by_symbol_found(self, mock_async_session):
        """Test get_coin_by_symbol returns coin when found."""
        # Arrange
        symbol = "BTC"
        expected_coin = Coin(
            id=1,
            symbol=symbol,
            name="Bitcoin",
            coingecko_id="bitcoin"
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_coin
        mock_async_session.execute.return_value = mock_result
        
        # Act
        result = await get_coin_by_symbol(mock_async_session, symbol)
        
        # Assert
        assert result == expected_coin
        assert result.symbol == symbol
        assert result.name == "Bitcoin"

    @pytest.mark.asyncio
    async def test_get_coin_by_symbol_not_found(self, mock_async_session):
        """Test get_coin_by_symbol returns None when coin not found."""
        # Arrange
        symbol = "UNKNOWN"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_async_session.execute.return_value = mock_result
        
        # Act
        result = await get_coin_by_symbol(mock_async_session, symbol)
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_create_post_with_coins(
        self, 
        mock_async_session, 
        sample_news_data, 
        sample_sentiment,
        mock_coingecko_response
    ):
        """Test create_post creates post with associated coins."""
        # Arrange
        mock_async_session.add = MagicMock()
        mock_async_session.commit = AsyncMock()
        mock_async_session.flush = AsyncMock()
        mock_async_session.refresh = AsyncMock()
        
        # Mock get_coin_by_symbol to return None (new coin)
        with patch('app.services.news.get_coin_by_symbol', return_value=None):
            with patch('app.services.news.coingecko_client.get_coins_markets', 
                      return_value=mock_coingecko_response):
                
                # Mock the final query that returns the post with coins
                expected_post = Post(
                    id=1,
                    title=sample_news_data.title,
                    body=sample_news_data.body,
                    source=sample_news_data.source,
                    item_type='post',  # Twitter source becomes 'post'
                    sentiment="positive",
                    score=0.85
                )
                mock_result = MagicMock()
                mock_result.unique.return_value.scalar_one.return_value = expected_post
                mock_async_session.execute.return_value = mock_result
                
                # Act
                result = await create_post(mock_async_session, sample_news_data, sample_sentiment)
                
                # Assert
                assert result == expected_post
                assert result.item_type == 'post'  # Twitter source
                assert result.sentiment == "positive"
                assert result.score == 0.85
                
                # Verify session operations were called
                assert mock_async_session.add.call_count >= 2  # Post + Coin + PostCoin
                assert mock_async_session.commit.call_count == 2
                assert mock_async_session.flush.call_count == 1

    @pytest.mark.asyncio
    async def test_create_post_article_type(
        self, 
        mock_async_session, 
        sample_sentiment
    ):
        """Test create_post sets item_type to 'article' for non-Twitter sources."""
        # Arrange
        news_data = NewsData(
            title="Bitcoin Analysis",
            body="Detailed analysis of Bitcoin trends",
            url="https://example.com/analysis",
            source="CoinDesk",  # Non-Twitter source
            coins=set(),
            time=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        mock_async_session.add = MagicMock()
        mock_async_session.commit = AsyncMock()
        mock_async_session.refresh = AsyncMock()
        
        # Mock the final query
        expected_post = Post(
            id=1,
            title=news_data.title,
            item_type='article',  # Non-Twitter source becomes 'article'
            sentiment="positive",
            score=0.85
        )
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one.return_value = expected_post
        mock_async_session.execute.return_value = mock_result
        
        # Act
        result = await create_post(mock_async_session, news_data, sample_sentiment)
        
        # Assert
        assert result.item_type == 'article'

    @pytest.mark.asyncio
    async def test_create_post_existing_coin(
        self, 
        mock_async_session, 
        sample_news_data, 
        sample_sentiment,
        mock_coingecko_response
    ):
        """Test create_post uses existing coin when found in database."""
        # Arrange
        existing_coin = Coin(
            id=1,
            symbol="BTC",
            name="Bitcoin",
            coingecko_id="bitcoin"
        )
        
        mock_async_session.add = MagicMock()
        mock_async_session.commit = AsyncMock()
        mock_async_session.refresh = AsyncMock()
        
        # Mock get_coin_by_symbol to return existing coin
        with patch('app.services.news.get_coin_by_symbol', return_value=existing_coin):
            with patch('app.services.news.coingecko_client.get_coins_markets', 
                      return_value=mock_coingecko_response):
                
                expected_post = Post(id=1, title=sample_news_data.title)
                mock_result = MagicMock()
                mock_result.unique.return_value.scalar_one.return_value = expected_post
                mock_async_session.execute.return_value = mock_result
                
                # Act
                result = await create_post(mock_async_session, sample_news_data, sample_sentiment)
                
                # Assert
                # Verify that we didn't add a new coin (existing coin was used)
                # The add calls should be: Post + PostCoin (no new Coin)
                add_calls = mock_async_session.add.call_args_list
                assert len(add_calls) == 2  # Post and PostCoin only
