"""
Integration tests for trending endpoints.

These tests validate the trending API endpoints by making HTTP requests
and verifying the responses. They use a real test database (in-memory) but 
mock external network calls.
"""
import pytest
from datetime import datetime, date, time, timezone, timedelta
from httpx import AsyncClient
from sqlmodel import select

from app.models.coin import Coin
from app.models.post import Post
from app.models.post_coin import PostCoin


@pytest.mark.integration
class TestTrendingCoins:
    """Test trending coins endpoint."""

    @pytest.fixture
    async def test_posts_for_trending(self, db_session, test_coins):
        """Create test posts from today with different sentiment and mention counts for trending."""
        posts = []
        today = date.today()
        start_of_day = datetime.combine(today, time.min, tzinfo=timezone.utc)
        
        # Get coins
        btc_coin = test_coins[0]  # Bitcoin
        eth_coin = test_coins[1]  # Ethereum
        ada_coin = test_coins[2]  # Cardano
        
        # Create posts for today with different mention patterns
        # Bitcoin: 4 posts with different sentiments (2 Bullish, 1 Bearish, 1 Neutral)
        btc_posts_data = [
            {"title": "Bitcoin breaks resistance!", "sentiment": "Bullish", "hours": 1},
            {"title": "BTC shows strong momentum", "sentiment": "Bullish", "hours": 2},
            {"title": "Bitcoin pullback expected", "sentiment": "Bearish", "hours": 3},
            {"title": "BTC consolidation phase", "sentiment": "Neutral", "hours": 4},
        ]
        
        # Ethereum: 2 posts (1 Bullish, 1 Neutral)
        eth_posts_data = [
            {"title": "Ethereum upgrade successful", "sentiment": "Bullish", "hours": 5},
            {"title": "ETH network activity stable", "sentiment": "Neutral", "hours": 6},
        ]
        
        # Cardano: 1 post (1 Bullish)
        ada_posts_data = [
            {"title": "Cardano development progress", "sentiment": "Bullish", "hours": 7},
        ]
        
        # Create Bitcoin posts
        for i, post_data in enumerate(btc_posts_data):
            post = Post(
                title=post_data["title"],
                body=f"Bitcoin analysis content {i}",
                url=f"https://example.com/btc-{i}",
                source="TestNews",
                item_type="article",
                feed="Sentix",
                sentiment=post_data["sentiment"],
                score=0.5 + (i * 0.1),
                time=start_of_day + timedelta(hours=post_data["hours"])
            )
            db_session.add(post)
            posts.append(post)
        
        # Create Ethereum posts
        for i, post_data in enumerate(eth_posts_data):
            post = Post(
                title=post_data["title"],
                body=f"Ethereum analysis content {i}",
                url=f"https://example.com/eth-{i}",
                source="TestNews",
                item_type="article", 
                feed="Sentix",
                sentiment=post_data["sentiment"],
                score=0.6 + (i * 0.1),
                time=start_of_day + timedelta(hours=post_data["hours"])
            )
            db_session.add(post)
            posts.append(post)
        
        # Create Cardano posts
        for i, post_data in enumerate(ada_posts_data):
            post = Post(
                title=post_data["title"],
                body=f"Cardano analysis content {i}",
                url=f"https://example.com/ada-{i}",
                source="TestNews",
                item_type="article",
                feed="Sentix", 
                sentiment=post_data["sentiment"],
                score=0.7 + (i * 0.1),
                time=start_of_day + timedelta(hours=post_data["hours"])
            )
            db_session.add(post)
            posts.append(post)
        
        await db_session.commit()
        
        # Create PostCoin relationships
        # Bitcoin (4 posts)
        for i in range(4):
            post_coin = PostCoin(post_id=posts[i].id, coin_id=btc_coin.id)
            db_session.add(post_coin)
        
        # Ethereum (2 posts)
        for i in range(4, 6):
            post_coin = PostCoin(post_id=posts[i].id, coin_id=eth_coin.id)
            db_session.add(post_coin)
        
        # Cardano (1 post)
        post_coin = PostCoin(post_id=posts[6].id, coin_id=ada_coin.id)
        db_session.add(post_coin)
        
        await db_session.commit()
        return posts

    @pytest.mark.asyncio
    async def test_get_trending_coins_success(self, authenticated_client: AsyncClient, test_posts_for_trending):
        """Test successful retrieval of trending coins."""
        response = await authenticated_client.get("/api/v1/trending/coins")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "items" in data
        assert "page" in data
        assert "page_size" in data
        assert "total" in data
        assert "total_pages" in data
        assert "has_next" in data
        assert "has_prev" in data
        
        # Check pagination defaults
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["has_prev"] is False
        
        # Check that coins are returned
        assert len(data["items"]) == 3  # BTC, ETH, ADA
        
        # Verify coins are ordered by mention count (descending)
        items = data["items"]
        assert items[0]["symbol"] == "BTC"  # 4 mentions (highest)
        assert items[0]["mention_count"] == 4
        assert items[1]["symbol"] == "ETH"  # 2 mentions (middle)
        assert items[1]["mention_count"] == 2
        assert items[2]["symbol"] == "ADA"  # 1 mention (lowest)
        assert items[2]["mention_count"] == 1
        
        # Check sentiment stats for Bitcoin (2 Bullish, 1 Bearish, 1 Neutral)
        btc_item = items[0]
        assert btc_item["sentiment_stats"]["positive"] == 2
        assert btc_item["sentiment_stats"]["negative"] == 1
        assert btc_item["sentiment_stats"]["neutral"] == 1
        
        # Check sentiment stats for Ethereum (1 Bullish, 1 Neutral)
        eth_item = items[1]
        assert eth_item["sentiment_stats"]["positive"] == 1
        assert eth_item["sentiment_stats"]["negative"] == 0
        assert eth_item["sentiment_stats"]["neutral"] == 1
        
        # Check sentiment stats for Cardano (1 Bullish)
        ada_item = items[2]
        assert ada_item["sentiment_stats"]["positive"] == 1
        assert ada_item["sentiment_stats"]["negative"] == 0
        assert ada_item["sentiment_stats"]["neutral"] == 0
        
        # Check that each item has required fields
        for item in items:
            assert "id" in item
            assert "symbol" in item
            assert "name" in item
            assert "image_url" in item
            assert "mention_count" in item
            assert "sentiment_stats" in item
            
            # Check sentiment_stats structure
            sentiment_stats = item["sentiment_stats"]
            assert "positive" in sentiment_stats
            assert "negative" in sentiment_stats
            assert "neutral" in sentiment_stats
            assert isinstance(sentiment_stats["positive"], int)
            assert isinstance(sentiment_stats["negative"], int)
            assert isinstance(sentiment_stats["neutral"], int)

    @pytest.mark.asyncio
    async def test_get_trending_coins_pagination(self, authenticated_client: AsyncClient, test_posts_for_trending):
        """Test trending coins pagination."""
        # Test with page_size=2 to verify pagination works
        response = await authenticated_client.get("/api/v1/trending/coins?page=1&page_size=2")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check pagination metadata
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total"] == 3  # Total coins with mentions today
        assert data["total_pages"] == 2  # ceil(3/2) = 2
        assert data["has_next"] is True
        assert data["has_prev"] is False
        
        # Check that only 2 items are returned (BTC and ETH)
        assert len(data["items"]) == 2
        assert data["items"][0]["symbol"] == "BTC"
        assert data["items"][1]["symbol"] == "ETH"
        
        # Test page 2
        response = await authenticated_client.get("/api/v1/trending/coins?page=2&page_size=2")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check pagination metadata for page 2
        assert data["page"] == 2
        assert data["page_size"] == 2
        assert data["total"] == 3
        assert data["total_pages"] == 2
        assert data["has_next"] is False
        assert data["has_prev"] is True
        
        # Check that only 1 item is returned (ADA)
        assert len(data["items"]) == 1
        assert data["items"][0]["symbol"] == "ADA"

    @pytest.mark.asyncio
    async def test_get_trending_coins_no_posts_today(self, authenticated_client: AsyncClient, test_coins):
        """Test trending coins when no posts exist for today."""
        response = await authenticated_client.get("/api/v1/trending/coins")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "items" in data
        assert data["total"] == 0
        assert data["total_pages"] == 0
        assert data["has_next"] is False
        assert data["has_prev"] is False
        assert len(data["items"]) == 0

    @pytest.fixture
    async def test_posts_from_yesterday(self, db_session, test_coins):
        """Create test posts from yesterday (should not appear in trending)."""
        posts = []
        yesterday = date.today() - timedelta(days=1)
        start_of_yesterday = datetime.combine(yesterday, time.min, tzinfo=timezone.utc)
        
        btc_coin = test_coins[0]  # Bitcoin
        
        # Create posts from yesterday
        for i in range(3):
            post = Post(
                title=f"Yesterday's Bitcoin News {i}",
                body=f"Bitcoin analysis from yesterday {i}",
                url=f"https://example.com/btc-yesterday-{i}",
                source="TestNews",
                item_type="article",
                feed="Sentix",
                sentiment="Bullish",
                score=0.8,
                time=start_of_yesterday + timedelta(hours=i)
            )
            db_session.add(post)
            posts.append(post)
        
        await db_session.commit()
        
        # Create PostCoin relationships
        for post in posts:
            post_coin = PostCoin(post_id=post.id, coin_id=btc_coin.id)
            db_session.add(post_coin)
        
        await db_session.commit()
        return posts

    @pytest.mark.asyncio
    async def test_get_trending_coins_filters_by_today(self, authenticated_client: AsyncClient, test_posts_from_yesterday):
        """Test that trending coins only includes posts from today."""
        response = await authenticated_client.get("/api/v1/trending/coins")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return no trending coins since posts are from yesterday
        assert data["total"] == 0
        assert len(data["items"]) == 0

    @pytest.mark.asyncio
    async def test_get_trending_coins_unauthorized(self, client: AsyncClient):
        """Test trending coins endpoint without authentication."""
        response = await client.get("/api/v1/trending/coins")
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_trending_coins_with_different_page_sizes(self, authenticated_client: AsyncClient, test_posts_for_trending):
        """Test trending coins with different page sizes."""
        # Test with page_size=1
        response = await authenticated_client.get("/api/v1/trending/coins?page_size=1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page_size"] == 1
        assert data["total_pages"] == 3  # ceil(3/1) = 3
        assert len(data["items"]) == 1
        assert data["items"][0]["symbol"] == "BTC"  # Highest mentions first
        
        # Test with page_size=10 (should return all)
        response = await authenticated_client.get("/api/v1/trending/coins?page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page_size"] == 10
        assert data["total_pages"] == 1  # ceil(3/10) = 1
        assert len(data["items"]) == 3
        assert data["has_next"] is False

    @pytest.mark.asyncio
    async def test_get_trending_coins_response_schema_validation(self, authenticated_client: AsyncClient, test_posts_for_trending):
        """Test that the response conforms to the expected schema."""
        response = await authenticated_client.get("/api/v1/trending/coins")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate top-level response structure (TrendingCoinsResponse)
        required_fields = ["items", "page", "page_size", "total", "total_pages", "has_next", "has_prev"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Validate that items is a list
        assert isinstance(data["items"], list)
        
        # Validate each coin item structure (TrendingCoin)
        for item in data["items"]:
            required_coin_fields = ["id", "symbol", "name", "image_url", "mention_count", "sentiment_stats"]
            for field in required_coin_fields:
                assert field in item, f"Missing required coin field: {field}"
            
            # Validate types
            assert isinstance(item["id"], int)
            assert isinstance(item["symbol"], str)
            assert isinstance(item["mention_count"], int)
            assert item["mention_count"] > 0  # Should only include coins with mentions
            
            # Validate sentiment_stats structure (SentimentStats)
            sentiment_stats = item["sentiment_stats"]
            required_sentiment_fields = ["positive", "negative", "neutral"]
            for field in required_sentiment_fields:
                assert field in sentiment_stats, f"Missing required sentiment field: {field}"
                assert isinstance(sentiment_stats[field], int)
                assert sentiment_stats[field] >= 0
