"""
Integration tests for news endpoints.

These tests validate the news API endpoints by making HTTP requests
and verifying the responses. They use a real test database (in-memory) but 
mock external network calls to CoinGecko.
"""
import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlmodel import select

from app.models.post import Post
from app.models.bookmark import PostBookmark


@pytest.mark.integration
class TestNewsFeed:
    """Test news feed endpoint (/api/v1/news/)."""

    @pytest.mark.asyncio
    async def test_get_news_feed_success(self, authenticated_client: AsyncClient, test_posts_for_pagination: list[Post]):
        """Test fetching the news feed with default pagination."""
        response = await authenticated_client.get("/api/v1/news/")
        
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
        
        # Check default pagination values
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total"] == 25  # We created 25 posts
        assert data["total_pages"] == 2  # 25 posts / 20 per page = 2 pages
        assert data["has_next"] is True  # Should have next page
        assert data["has_prev"] is False  # First page, no previous
        
        # Check items
        assert len(data["items"]) == 20  # Should return first 20 posts
        
        # Verify posts are ordered by time (newest first)
        items = data["items"]
        for i in range(1, len(items)):
            current_time = datetime.fromisoformat(items[i]["time"].replace("Z", "+00:00"))
            previous_time = datetime.fromisoformat(items[i-1]["time"].replace("Z", "+00:00"))
            assert current_time <= previous_time
        
        # Check post structure
        first_post = items[0]
        assert "id" in first_post
        assert "title" in first_post
        assert "body" in first_post
        assert "url" in first_post
        assert "source" in first_post
        assert "time" in first_post
        assert "coins" in first_post
        assert "is_bookmarked" in first_post
        assert "sentiment" in first_post
        assert "score" in first_post
        assert first_post["is_bookmarked"] is False  # No bookmarks created yet

    @pytest.mark.asyncio
    async def test_get_news_feed_pagination(self, authenticated_client: AsyncClient, test_posts_for_pagination: list[Post]):
        """Test news feed pagination with custom page size."""
        response = await authenticated_client.get("/api/v1/news/?page=2&page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 2
        assert data["page_size"] == 10
        assert data["total"] == 25
        assert data["total_pages"] == 3  # 25 posts / 10 per page = 3 pages
        assert data["has_next"] is True  # Should have page 3
        assert data["has_prev"] is True  # Should have page 1
        assert len(data["items"]) == 10

    @pytest.mark.asyncio
    async def test_get_news_feed_filter_by_coin(self, authenticated_client: AsyncClient, test_posts_for_pagination: list[Post]):
        """Test filtering news feed by coin symbol."""
        response = await authenticated_client.get("/api/v1/news/?coin=BTC")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only return posts associated with Bitcoin
        # Since we alternate between BTC and ETH, we should have roughly half
        assert data["total"] > 0
        assert data["total"] < 25  # Less than total posts
        
        # Verify all returned posts have Bitcoin in their coins
        for item in data["items"]:
            coin_symbols = [coin["symbol"] for coin in item["coins"]]
            assert "BTC" in coin_symbols

    @pytest.mark.asyncio
    async def test_get_news_feed_filter_by_date_range(self, authenticated_client: AsyncClient, test_posts_with_sentiment: list[Post]):
        """Test filtering news feed by date range."""
        # Filter to get posts from the last 3 days
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=3)
        
        # Format dates for API (without timezone info)
        start_date_str = start_date.replace(tzinfo=None).isoformat()
        end_date_str = end_date.replace(tzinfo=None).isoformat()
        
        response = await authenticated_client.get(
            f"/api/v1/news/?start_date={start_date_str}&end_date={end_date_str}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return posts within the date range
        assert data["total"] > 0
        assert data["total"] <= 14  # We created 14 posts over 7 days, so max 8 in 3 days
        
        # Verify all posts are within the date range
        for item in data["items"]:
            post_time = datetime.fromisoformat(item["time"].replace("Z", "+00:00"))
            # Convert to naive datetime for comparison with our range
            post_time_naive = post_time.replace(tzinfo=None)
            start_date_naive = start_date.replace(tzinfo=None)
            end_date_naive = end_date.replace(tzinfo=None)
            assert start_date_naive <= post_time_naive <= end_date_naive

    @pytest.mark.asyncio
    async def test_get_news_feed_with_bookmarks(self, authenticated_client: AsyncClient, test_post: Post, test_bookmark: PostBookmark, db_session):
        """Test that bookmarked posts show is_bookmarked=true."""
        response = await authenticated_client.get("/api/v1/news/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Find the bookmarked post in the response
        bookmarked_post = next((item for item in data["items"] if item["id"] == test_post.id), None)
        assert bookmarked_post is not None
        assert bookmarked_post["is_bookmarked"] is True

    @pytest.mark.asyncio
    async def test_get_news_feed_empty_result(self, authenticated_client: AsyncClient):
        """Test news feed with no posts returns empty pagination."""
        response = await authenticated_client.get("/api/v1/news/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 0
        assert data["total_pages"] == 0
        assert data["has_next"] is False
        assert data["has_prev"] is False
        assert len(data["items"]) == 0

    @pytest.mark.asyncio
    async def test_get_news_feed_unauthorized(self, client: AsyncClient):
        """Test that unauthenticated requests are rejected."""
        response = await client.get("/api/v1/news/")
        
        assert response.status_code == 401


@pytest.mark.integration
class TestNewsSearch:
    """Test news search endpoint (/api/v1/news/search)."""

    @pytest.mark.asyncio
    async def test_search_news_by_title(self, authenticated_client: AsyncClient, test_posts_for_search: list[Post]):
        """Test searching news by title keyword."""
        response = await authenticated_client.get("/api/v1/news/search?query=Bitcoin")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find posts with "Bitcoin" in title
        assert data["total"] > 0
        
        # Verify search results contain the query term
        for item in data["items"]:
            title_or_body = f"{item['title']} {item['body']}".lower()
            assert "bitcoin" in title_or_body

    @pytest.mark.asyncio
    async def test_search_news_by_body_content(self, authenticated_client: AsyncClient, test_posts_for_search: list[Post]):
        """Test searching news by body content."""
        response = await authenticated_client.get("/api/v1/news/search?query=smart%20contracts")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find posts with "smart contracts" in body
        assert data["total"] > 0
        
        for item in data["items"]:
            title_or_body = f"{item['title']} {item['body']}".lower()
            assert "smart contracts" in title_or_body

    @pytest.mark.asyncio
    async def test_search_news_case_insensitive(self, authenticated_client: AsyncClient, test_posts_for_search: list[Post]):
        """Test that search is case insensitive."""
        response = await authenticated_client.get("/api/v1/news/search?query=ETHEREUM")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] > 0
        
        for item in data["items"]:
            title_or_body = f"{item['title']} {item['body']}".lower()
            assert "ethereum" in title_or_body

    @pytest.mark.asyncio
    async def test_search_news_with_pagination(self, authenticated_client: AsyncClient, test_posts_for_search: list[Post]):
        """Test search with pagination parameters."""
        response = await authenticated_client.get("/api/v1/news/search?query=news&page=1&page_size=2")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 1
        assert data["page_size"] == 2
        if data["total"] > 0:
            assert len(data["items"]) <= 2

    @pytest.mark.asyncio
    async def test_search_news_with_coin_filter(self, authenticated_client: AsyncClient, test_posts_for_search: list[Post]):
        """Test search combined with coin filtering."""
        response = await authenticated_client.get("/api/v1/news/search?query=analysis&coin=BTC")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find posts with "analysis" that are also associated with Bitcoin
        for item in data["items"]:
            title_or_body = f"{item['title']} {item['body']}".lower()
            assert "analysis" in title_or_body
            
            coin_symbols = [coin["symbol"] for coin in item["coins"]]
            assert "BTC" in coin_symbols

    @pytest.mark.asyncio
    async def test_search_news_with_date_filter(self, authenticated_client: AsyncClient, test_posts_for_search: list[Post]):
        """Test search combined with date filtering."""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(hours=1)
        
        # Format dates for API (without timezone info)
        start_date_str = start_date.replace(tzinfo=None).isoformat()
        end_date_str = end_date.replace(tzinfo=None).isoformat()
        
        response = await authenticated_client.get(
            f"/api/v1/news/search?query=news&start_date={start_date_str}&end_date={end_date_str}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify date filtering is applied
        for item in data["items"]:
            post_time = datetime.fromisoformat(item["time"].replace("Z", "+00:00"))
            # Convert to naive datetime for comparison
            post_time_naive = post_time.replace(tzinfo=None)
            start_date_naive = start_date.replace(tzinfo=None)
            end_date_naive = end_date.replace(tzinfo=None)
            assert start_date_naive <= post_time_naive <= end_date_naive

    @pytest.mark.asyncio
    async def test_search_news_no_results(self, authenticated_client: AsyncClient, test_posts_for_search: list[Post]):
        """Test search with query that returns no results."""
        response = await authenticated_client.get("/api/v1/news/search?query=nonexistentterm")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 0
        assert len(data["items"]) == 0

    @pytest.mark.asyncio
    async def test_search_news_missing_query(self, authenticated_client: AsyncClient):
        """Test search without query parameter returns validation error."""
        response = await authenticated_client.get("/api/v1/news/search")
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_search_news_empty_query(self, authenticated_client: AsyncClient):
        """Test search with empty query returns validation error."""
        response = await authenticated_client.get("/api/v1/news/search?query=")
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_search_news_unauthorized(self, client: AsyncClient):
        """Test that unauthenticated search requests are rejected."""
        response = await client.get("/api/v1/news/search?query=bitcoin")
        
        assert response.status_code == 401


@pytest.mark.integration
class TestSinglePost:
    """Test single post endpoint (/api/v1/news/{post_id})."""

    @pytest.mark.asyncio
    async def test_get_post_by_id_success(self, authenticated_client: AsyncClient, test_post: Post):
        """Test fetching a single post by ID."""
        response = await authenticated_client.get(f"/api/v1/news/{test_post.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify post data
        assert data["id"] == test_post.id
        assert data["title"] == test_post.title
        assert data["body"] == test_post.body
        assert data["url"] == test_post.url
        assert data["source"] == test_post.source
        assert data["sentiment"] == test_post.sentiment
        assert data["score"] == test_post.score
        assert "coins" in data
        assert "is_bookmarked" in data
        assert data["is_bookmarked"] is False  # No bookmark created

    @pytest.mark.asyncio
    async def test_get_post_with_bookmark(self, authenticated_client: AsyncClient, test_post: Post, test_bookmark: PostBookmark):
        """Test fetching a post that is bookmarked by the user."""
        response = await authenticated_client.get(f"/api/v1/news/{test_post.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_post.id
        assert data["is_bookmarked"] is True

    @pytest.mark.asyncio
    async def test_get_post_with_coins(self, authenticated_client: AsyncClient, test_post: Post):
        """Test that post coins are properly included."""
        response = await authenticated_client.get(f"/api/v1/news/{test_post.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "coins" in data
        assert len(data["coins"]) > 0
        
        # Check coin structure
        coin = data["coins"][0]
        assert "id" in coin
        assert "symbol" in coin
        assert "name" in coin

    @pytest.mark.asyncio
    async def test_get_post_not_found(self, authenticated_client: AsyncClient):
        """Test fetching a non-existent post returns 404."""
        non_existent_id = 99999
        response = await authenticated_client.get(f"/api/v1/news/{non_existent_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Post not found"

    @pytest.mark.asyncio
    async def test_get_post_invalid_id(self, authenticated_client: AsyncClient):
        """Test fetching a post with invalid ID format."""
        response = await authenticated_client.get("/api/v1/news/invalid-id")
        
        assert response.status_code == 422  # Validation error for invalid int

    @pytest.mark.asyncio
    async def test_get_post_unauthorized(self, client: AsyncClient, test_post: Post):
        """Test that unauthenticated requests are rejected."""
        response = await client.get(f"/api/v1/news/{test_post.id}")
        
        assert response.status_code == 401


@pytest.mark.integration
class TestNewsEndpointEdgeCases:
    """Test edge cases and error scenarios for news endpoints."""

    @pytest.mark.asyncio
    async def test_news_feed_large_page_number(self, authenticated_client: AsyncClient, test_posts_for_pagination: list[Post]):
        """Test requesting a page number beyond available pages."""
        response = await authenticated_client.get("/api/v1/news/?page=999")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 999
        assert len(data["items"]) == 0  # No items on this page
        assert data["has_next"] is False
        assert data["has_prev"] is True

    @pytest.mark.asyncio
    async def test_news_feed_invalid_page_size(self, authenticated_client: AsyncClient):
        """Test with invalid page size parameters."""
        response = await authenticated_client.get("/api/v1/news/?page_size=0")
        
        # This should either return 422 validation error or handle gracefully
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_news_feed_malformed_date(self, authenticated_client: AsyncClient):
        """Test with malformed date parameters."""
        response = await authenticated_client.get("/api/v1/news/?start_date=invalid-date")
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_search_very_long_query(self, authenticated_client: AsyncClient, test_posts_for_search: list[Post]):
        """Test search with very long query string."""
        long_query = "a" * 1000  # Very long query
        response = await authenticated_client.get(f"/api/v1/news/search?query={long_query}")
        
        assert response.status_code == 200
        data = response.json()
        # Should handle gracefully, likely returning no results
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_search_special_characters(self, authenticated_client: AsyncClient, test_posts_for_search: list[Post]):
        """Test search with special characters."""
        special_query = "test@#$%^&*()_+"
        response = await authenticated_client.get(f"/api/v1/news/search?query={special_query}")
        
        assert response.status_code == 200
        data = response.json()
        # Should handle special characters gracefully
        assert "total" in data

    @pytest.mark.asyncio
    async def test_coin_filter_nonexistent_coin(self, authenticated_client: AsyncClient, test_posts_for_pagination: list[Post]):
        """Test filtering by a coin that doesn't exist."""
        response = await authenticated_client.get("/api/v1/news/?coin=NONEXISTENT")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 0
        assert len(data["items"]) == 0

    @pytest.mark.asyncio
    async def test_multiple_filters_combined(self, authenticated_client: AsyncClient, test_posts_for_search: list[Post]):
        """Test combining multiple filters together."""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=1)
        
        # Format dates for API (without timezone info)
        start_date_str = start_date.replace(tzinfo=None).isoformat()
        end_date_str = end_date.replace(tzinfo=None).isoformat()
        
        response = await authenticated_client.get(
            f"/api/v1/news/search?query=analysis&coin=BTC&start_date={start_date_str}&end_date={end_date_str}&page=1&page_size=5"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should apply all filters correctly
        assert "total" in data
        assert "items" in data
        assert data["page"] == 1
        assert data["page_size"] == 5
