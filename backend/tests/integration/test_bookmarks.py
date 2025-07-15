"""
Integration tests for bookmark endpoints.

These tests validate the bookmark API endpoints by making HTTP requests
and verifying the responses. They use a real test database (in-memory) but 
mock external network calls.
"""
import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bookmark import PostBookmark
from app.models.post import Post
from app.models.user import User


@pytest.mark.integration
class TestBookmarkCreation:
    """Test bookmark creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_bookmark_success(
        self, 
        authenticated_client: AsyncClient, 
        test_user: User, 
        test_post: Post, 
        db_session: AsyncSession
    ):
        """Test successful bookmark creation."""
        bookmark_data = {"post_id": test_post.id}
        
        response = await authenticated_client.post("/api/v1/bookmarks/", json=bookmark_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Check response structure
        assert "id" in data
        assert "user_id" in data
        assert "post_id" in data
        assert "created_at" in data
        
        # Check response data
        assert data["user_id"] == test_user.id
        assert data["post_id"] == test_post.id
        
        # Verify bookmark was created in database
        stmt = select(PostBookmark).where(
            PostBookmark.user_id == test_user.id,
            PostBookmark.post_id == test_post.id
        )
        result = await db_session.execute(stmt)
        bookmark = result.scalar_one_or_none()
        
        assert bookmark is not None
        assert bookmark.user_id == test_user.id
        assert bookmark.post_id == test_post.id

    @pytest.mark.asyncio
    async def test_create_bookmark_duplicate(
        self, 
        authenticated_client: AsyncClient, 
        test_user: User, 
        test_bookmark: PostBookmark,
        db_session: AsyncSession
    ):
        """Test creating a duplicate bookmark returns existing bookmark."""
        # Refresh the bookmark to avoid lazy loading issues
        await db_session.refresh(test_bookmark)
        user_id = test_user.id  # Get user ID before making the request
        
        bookmark_data = {"post_id": test_bookmark.post_id}
        
        response = await authenticated_client.post("/api/v1/bookmarks/", json=bookmark_data)
        
        # Should return the existing bookmark, not create a new one
        assert response.status_code == 201
        data = response.json()
        
        assert data["id"] == test_bookmark.id
        assert data["user_id"] == user_id
        assert data["post_id"] == test_bookmark.post_id

    @pytest.mark.asyncio
    async def test_create_bookmark_nonexistent_post(
        self, 
        authenticated_client: AsyncClient
    ):
        """Test creating bookmark for non-existent post."""
        bookmark_data = {"post_id": 99999}  # Non-existent post ID
        
        response = await authenticated_client.post("/api/v1/bookmarks/", json=bookmark_data)
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Post not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_bookmark_unauthenticated(
        self, 
        client: AsyncClient, 
        test_post: Post
    ):
        """Test creating bookmark without authentication."""
        bookmark_data = {"post_id": test_post.id}
        
        response = await client.post("/api/v1/bookmarks/", json=bookmark_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_create_bookmark_invalid_data(
        self, 
        authenticated_client: AsyncClient
    ):
        """Test creating bookmark with invalid data."""
        # Missing post_id
        response = await authenticated_client.post("/api/v1/bookmarks/", json={})
        assert response.status_code == 422
        
        # Invalid post_id type
        response = await authenticated_client.post("/api/v1/bookmarks/", json={"post_id": "invalid"})
        assert response.status_code == 422


@pytest.mark.integration
class TestBookmarkDeletion:
    """Test bookmark deletion endpoint."""

    @pytest.mark.asyncio
    async def test_delete_bookmark_success(
        self, 
        authenticated_client: AsyncClient, 
        test_bookmark: PostBookmark, 
        db_session: AsyncSession
    ):
        """Test successful bookmark deletion."""
        response = await authenticated_client.delete(f"/api/v1/bookmarks/{test_bookmark.post_id}")
        
        assert response.status_code == 204
        assert response.content == b""  # No content for 204
        
        # Verify bookmark was deleted from database
        stmt = select(PostBookmark).where(PostBookmark.id == test_bookmark.id)
        result = await db_session.execute(stmt)
        bookmark = result.scalar_one_or_none()
        
        assert bookmark is None

    @pytest.mark.asyncio
    async def test_delete_bookmark_not_found(
        self, 
        authenticated_client: AsyncClient
    ):
        """Test deleting non-existent bookmark."""
        non_existent_post_id = 99999
        
        response = await authenticated_client.delete(f"/api/v1/bookmarks/{non_existent_post_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Bookmark not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_delete_bookmark_other_user(
        self, 
        client: AsyncClient, 
        test_bookmark: PostBookmark, 
        db_session: AsyncSession
    ):
        """Test deleting bookmark belonging to another user."""
        # Create another user
        from app.core.security import get_password_hash
        from app.core.security import create_access_token
        
        other_user = User(
            email="other@example.com",
            username="otheruser",
            password=get_password_hash("OtherPass123!"),
            full_name="Other User"
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)
        
        # Create token for other user
        other_token = create_access_token(subject=other_user.id)
        client.headers.update({"Authorization": f"Bearer {other_token}"})
        
        response = await client.delete(f"/api/v1/bookmarks/{test_bookmark.post_id}")
        
        # Should return 404 since the bookmark doesn't belong to this user
        assert response.status_code == 404
        data = response.json()
        assert "Bookmark not found" in data["detail"]
        
        # Verify original bookmark still exists
        stmt = select(PostBookmark).where(PostBookmark.id == test_bookmark.id)
        result = await db_session.execute(stmt)
        bookmark = result.scalar_one_or_none()
        assert bookmark is not None

    @pytest.mark.asyncio
    async def test_delete_bookmark_unauthenticated(
        self, 
        client: AsyncClient, 
        test_bookmark: PostBookmark
    ):
        """Test deleting bookmark without authentication."""
        response = await client.delete(f"/api/v1/bookmarks/{test_bookmark.post_id}")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_delete_bookmark_invalid_post_id(
        self, 
        authenticated_client: AsyncClient
    ):
        """Test deleting bookmark with invalid post ID."""
        response = await authenticated_client.delete("/api/v1/bookmarks/invalid")
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


@pytest.mark.integration
class TestBookmarkList:
    """Test bookmark list endpoint."""

    @pytest.mark.asyncio
    async def test_get_bookmarked_posts_success(
        self, 
        authenticated_client: AsyncClient, 
        test_user: User, 
        db_session: AsyncSession
    ):
        """Test fetching user's bookmarked posts."""
        from datetime import datetime, timezone
        
        # Create multiple posts and bookmarks
        posts = []
        bookmarks = []
        
        base_time = datetime.now(timezone.utc)
        
        for i in range(3):
            post = Post(
                title=f"Test Post {i+1}",
                body=f"This is test post {i+1}",
                url=f"https://example.com/post-{i+1}",
                source="TestNews",
                item_type="article",
                feed="Sentix",
                sentiment="positive",
                score=0.5 + i * 0.1,
                time=base_time  # Use actual datetime
            )
            db_session.add(post)
            posts.append(post)
        
        await db_session.commit()
        
        # Create bookmarks for all posts
        for post in posts:
            await db_session.refresh(post)
            bookmark = PostBookmark(user_id=test_user.id, post_id=post.id)
            db_session.add(bookmark)
            bookmarks.append(bookmark)
        
        await db_session.commit()
        
        response = await authenticated_client.get("/api/v1/bookmarks/")
        
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
        assert data["total"] == 3
        assert data["total_pages"] == 1
        assert data["has_next"] is False
        assert data["has_prev"] is False
        
        # Check items
        items = data["items"]
        assert len(items) == 3
        
        # Check each item has required fields
        for item in items:
            assert "id" in item  # Post ID
            assert "title" in item
            assert "body" in item
            assert "url" in item
            assert "bookmark_id" in item
            assert "bookmarked_at" in item
            # Note: is_bookmarked field is added by the service for bookmarked posts
            # and should be True for all items in the bookmarks list

    @pytest.mark.asyncio
    async def test_get_bookmarked_posts_pagination(
        self, 
        authenticated_client: AsyncClient, 
        test_user: User, 
        db_session: AsyncSession
    ):
        """Test pagination of bookmarked posts."""
        from datetime import datetime, timezone, timedelta
        
        # Create 25 posts and bookmarks (more than default page size of 20)
        posts = []
        
        base_time = datetime.now(timezone.utc)
        
        for i in range(25):
            post = Post(
                title=f"Bookmark Test Post {i+1}",
                body=f"This is bookmark test post {i+1}",
                url=f"https://example.com/bookmark-post-{i+1}",
                source="TestNews",
                item_type="article",
                feed="Sentix",
                sentiment="positive",
                score=0.1 + i * 0.01,
                time=base_time - timedelta(hours=i)  # Use actual datetime with variation
            )
            db_session.add(post)
            posts.append(post)
        
        await db_session.commit()
        
        # Create bookmarks for all posts
        for post in posts:
            await db_session.refresh(post)
            bookmark = PostBookmark(user_id=test_user.id, post_id=post.id)
            db_session.add(bookmark)
        
        await db_session.commit()
        
        # Test first page
        response = await authenticated_client.get("/api/v1/bookmarks/?page=1&page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["total"] == 25
        assert data["total_pages"] == 3
        assert data["has_next"] is True
        assert data["has_prev"] is False
        assert len(data["items"]) == 10
        
        # Test second page
        response = await authenticated_client.get("/api/v1/bookmarks/?page=2&page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 2
        assert data["page_size"] == 10
        assert data["total"] == 25
        assert data["total_pages"] == 3
        assert data["has_next"] is True
        assert data["has_prev"] is True
        assert len(data["items"]) == 10
        
        # Test last page
        response = await authenticated_client.get("/api/v1/bookmarks/?page=3&page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 3
        assert data["page_size"] == 10
        assert data["total"] == 25
        assert data["total_pages"] == 3
        assert data["has_next"] is False
        assert data["has_prev"] is True
        assert len(data["items"]) == 5  # Last page has remaining items

    @pytest.mark.asyncio
    async def test_get_bookmarked_posts_empty(
        self, 
        authenticated_client: AsyncClient
    ):
        """Test fetching bookmarked posts when user has no bookmarks."""
        response = await authenticated_client.get("/api/v1/bookmarks/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 1
        assert data["total"] == 0
        assert data["total_pages"] == 0
        assert data["has_next"] is False
        assert data["has_prev"] is False
        assert len(data["items"]) == 0

    @pytest.mark.asyncio
    async def test_get_bookmarked_posts_ordering(
        self, 
        authenticated_client: AsyncClient, 
        test_user: User, 
        db_session: AsyncSession
    ):
        """Test that bookmarked posts are ordered by bookmark creation time (newest first)."""
        import asyncio
        from datetime import datetime, timezone, timedelta
        
        # Create posts
        posts = []
        base_time = datetime.now(timezone.utc)
        
        for i in range(3):
            post = Post(
                title=f"Ordered Post {i+1}",
                body=f"This is ordered post {i+1}",
                url=f"https://example.com/ordered-post-{i+1}",
                source="TestNews",
                item_type="article",
                feed="Sentix",
                sentiment="positive",
                score=0.5,
                time=base_time - timedelta(minutes=i)  # Use actual datetime
            )
            db_session.add(post)
            posts.append(post)
        
        await db_session.commit()
        
        # Create bookmarks with different timestamps (in reverse order)
        bookmark_base_time = datetime.now(timezone.utc)
        for i, post in enumerate(posts):
            await db_session.refresh(post)
            bookmark = PostBookmark(
                user_id=test_user.id, 
                post_id=post.id
            )
            # Manually set created_at for testing order
            bookmark.created_at = bookmark_base_time - timedelta(hours=i)
            db_session.add(bookmark)
            # Small delay to ensure different timestamps
            await asyncio.sleep(0.01)
        
        await db_session.commit()
        
        response = await authenticated_client.get("/api/v1/bookmarks/")
        
        assert response.status_code == 200
        data = response.json()
        
        items = data["items"]
        assert len(items) == 3
        
        # Should be ordered by bookmark creation time (newest first)
        # The first bookmark created was for posts[0], but it has the oldest timestamp
        # So posts[2] (newest bookmark) should come first
        assert items[0]["title"] == "Ordered Post 1"  # Most recent bookmark
        assert items[1]["title"] == "Ordered Post 2"
        assert items[2]["title"] == "Ordered Post 3"  # Oldest bookmark

    @pytest.mark.asyncio
    async def test_get_bookmarked_posts_unauthenticated(
        self, 
        client: AsyncClient
    ):
        """Test fetching bookmarked posts without authentication."""
        response = await client.get("/api/v1/bookmarks/")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_bookmarked_posts_invalid_pagination(
        self, 
        authenticated_client: AsyncClient
    ):
        """Test fetching bookmarked posts with invalid pagination parameters."""
        # Test negative page
        response = await authenticated_client.get("/api/v1/bookmarks/?page=-1")
        assert response.status_code == 422
        
        # Test zero page
        response = await authenticated_client.get("/api/v1/bookmarks/?page=0")
        assert response.status_code == 422
        
        # Test negative page_size
        response = await authenticated_client.get("/api/v1/bookmarks/?page_size=-1")
        assert response.status_code == 422
        
        # Test zero page_size
        response = await authenticated_client.get("/api/v1/bookmarks/?page_size=0")
        assert response.status_code == 422
        
        # Test excessive page_size
        response = await authenticated_client.get("/api/v1/bookmarks/?page_size=1000")
        assert response.status_code == 422
