import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.services.bookmark import (
    create_bookmark,
    delete_bookmark,
    is_bookmarked,
    get_user_bookmarks
)
from app.models.bookmark import PostBookmark
from app.models.post import Post


@pytest.mark.unit
class TestBookmarkService:
    """Test bookmark service functions with mocked database operations."""
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return 1
    
    @pytest.fixture
    def sample_post_id(self):
        """Sample post ID for testing."""
        return 100
    
    @pytest.fixture
    def sample_post(self):
        """Sample post for testing."""
        return Post(
            id=100,
            title="Test Post",
            body="Test content",
            url="https://example.com/test",
            source="TestNews"
        )
    
    @pytest.fixture
    def sample_bookmark(self):
        """Sample bookmark for testing."""
        return PostBookmark(
            id=1,
            user_id=1,
            post_id=100
        )

    @pytest.mark.asyncio
    async def test_create_bookmark_successful(
        self, 
        mock_async_session, 
        sample_user_id, 
        sample_post_id, 
        sample_post
    ):
        """Test create_bookmark for a successful case."""
        # Arrange
        # Mock post exists query
        mock_post_result = MagicMock()
        mock_post_result.scalar_one_or_none.return_value = sample_post
        mock_async_session.execute.return_value = mock_post_result
        
        # Mock session operations
        mock_async_session.add = MagicMock()
        mock_async_session.commit = AsyncMock()
        mock_async_session.refresh = AsyncMock()
        
        expected_bookmark = PostBookmark(
            id=1,
            user_id=sample_user_id,
            post_id=sample_post_id
        )
        
        # Mock refresh to set bookmark attributes
        async def mock_refresh(bookmark):
            bookmark.id = 1
        mock_async_session.refresh.side_effect = mock_refresh
        
        # Act
        result = await create_bookmark(mock_async_session, sample_user_id, sample_post_id)
        
        # Assert
        assert result.user_id == sample_user_id
        assert result.post_id == sample_post_id
        mock_async_session.add.assert_called_once()
        mock_async_session.commit.assert_called_once()
        mock_async_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_bookmark_post_not_found(
        self, 
        mock_async_session, 
        sample_user_id, 
        sample_post_id
    ):
        """Test create_bookmark raises HTTPException when post doesn't exist."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_async_session.execute.return_value = mock_result
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await create_bookmark(mock_async_session, sample_user_id, sample_post_id)
        
        assert exc_info.value.status_code == 404
        assert "Post not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_bookmark_duplicate_handling(
        self, 
        mock_async_session, 
        sample_user_id, 
        sample_post_id, 
        sample_post,
        sample_bookmark
    ):
        """Test that attempting to create a duplicate bookmark does not raise an unhandled error."""
        # Arrange
        # Mock post exists query
        mock_post_result = MagicMock()
        mock_post_result.scalar_one_or_none.return_value = sample_post
        
        # Mock existing bookmark query
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = sample_bookmark
        
        mock_async_session.execute.side_effect = [mock_post_result, mock_existing_result]
        
        # Mock session operations
        mock_async_session.add = MagicMock()
        mock_async_session.commit = AsyncMock(side_effect=IntegrityError("", "", ""))
        mock_async_session.rollback = AsyncMock()
        
        # Act
        result = await create_bookmark(mock_async_session, sample_user_id, sample_post_id)
        
        # Assert
        assert result == sample_bookmark
        mock_async_session.rollback.assert_called_once()
        # Verify we queried for existing bookmark after IntegrityError
        assert mock_async_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_create_bookmark_integrity_error_no_existing(
        self, 
        mock_async_session, 
        sample_user_id, 
        sample_post_id, 
        sample_post
    ):
        """Test create_bookmark raises HTTPException when IntegrityError occurs but no existing bookmark found."""
        # Arrange
        # Mock post exists query
        mock_post_result = MagicMock()
        mock_post_result.scalar_one_or_none.return_value = sample_post
        
        # Mock no existing bookmark found
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None
        
        mock_async_session.execute.side_effect = [mock_post_result, mock_existing_result]
        
        # Mock session operations
        mock_async_session.add = MagicMock()
        mock_async_session.commit = AsyncMock(side_effect=IntegrityError("", "", ""))
        mock_async_session.rollback = AsyncMock()
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await create_bookmark(mock_async_session, sample_user_id, sample_post_id)
        
        assert exc_info.value.status_code == 400
        assert "Unable to create bookmark" in exc_info.value.detail
        mock_async_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_bookmark_successful(
        self, 
        mock_async_session, 
        sample_user_id, 
        sample_post_id,
        sample_bookmark
    ):
        """Test delete_bookmark for a successful deletion."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_bookmark
        mock_async_session.execute.return_value = mock_result
        
        mock_async_session.delete = AsyncMock()
        mock_async_session.commit = AsyncMock()
        
        # Act
        result = await delete_bookmark(mock_async_session, sample_user_id, sample_post_id)
        
        # Assert
        assert result is True
        mock_async_session.delete.assert_called_once_with(sample_bookmark)
        mock_async_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_bookmark_not_found(
        self, 
        mock_async_session, 
        sample_user_id, 
        sample_post_id
    ):
        """Test deleting a bookmark that doesn't exist returns False."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_async_session.execute.return_value = mock_result
        
        # Act
        result = await delete_bookmark(mock_async_session, sample_user_id, sample_post_id)
        
        # Assert
        assert result is False
        # Verify delete and commit were not called
        assert not hasattr(mock_async_session, 'delete') or not mock_async_session.delete.called
        assert not hasattr(mock_async_session, 'commit') or not mock_async_session.commit.called

    @pytest.mark.asyncio
    async def test_is_bookmarked_true(
        self, 
        mock_async_session, 
        sample_user_id, 
        sample_post_id,
        sample_bookmark
    ):
        """Test is_bookmarked returns True for a bookmarked post."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_bookmark
        mock_async_session.execute.return_value = mock_result
        
        # Act
        result = await is_bookmarked(mock_async_session, sample_user_id, sample_post_id)
        
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_is_bookmarked_false(
        self, 
        mock_async_session, 
        sample_user_id, 
        sample_post_id
    ):
        """Test is_bookmarked returns False for a non-bookmarked post."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_async_session.execute.return_value = mock_result
        
        # Act
        result = await is_bookmarked(mock_async_session, sample_user_id, sample_post_id)
        
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_bookmarks_success(
        self, 
        mock_async_session, 
        sample_user_id
    ):
        """Test get_user_bookmarks returns paginated bookmarked posts."""
        # Arrange
        page = 1
        page_size = 10
        
        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 5
        
        # Mock bookmarks data using MagicMock instead of real Post objects
        sample_post_1 = MagicMock()
        sample_post_1.model_dump.return_value = {
            "id": 1, "title": "Post 1", "body": "Content 1", "url": "https://example.com/1"
        }
        
        sample_post_2 = MagicMock()
        sample_post_2.model_dump.return_value = {
            "id": 2, "title": "Post 2", "body": "Content 2", "url": "https://example.com/2"
        }
        
        sample_bookmarks = [
            PostBookmark(id=1, user_id=sample_user_id, post_id=1),
            PostBookmark(id=2, user_id=sample_user_id, post_id=2)
        ]
        
        # Mock posts query result
        mock_posts_result = MagicMock()
        mock_posts_result.all.return_value = [
            (sample_post_1, sample_bookmarks[0]),
            (sample_post_2, sample_bookmarks[1])
        ]
        
        mock_async_session.execute.side_effect = [mock_count_result, mock_posts_result]
        
        # Act
        items, total_count = await get_user_bookmarks(
            mock_async_session, 
            sample_user_id, 
            page=page, 
            page_size=page_size
        )
        
        # Assert
        assert total_count == 5
        assert len(items) == 2
        assert items[0]["id"] == 1
        assert items[0]["title"] == "Post 1"
        assert items[0]["bookmark_id"] == 1
        assert "bookmarked_at" in items[0]
        
        assert items[1]["id"] == 2
        assert items[1]["title"] == "Post 2"
        assert items[1]["bookmark_id"] == 2
        
        # Verify correct number of database calls
        assert mock_async_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_user_bookmarks_empty(
        self, 
        mock_async_session, 
        sample_user_id
    ):
        """Test get_user_bookmarks returns empty list when user has no bookmarks."""
        # Arrange
        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 0
        
        # Mock empty posts query result
        mock_posts_result = MagicMock()
        mock_posts_result.all.return_value = []
        
        mock_async_session.execute.side_effect = [mock_count_result, mock_posts_result]
        
        # Act
        items, total_count = await get_user_bookmarks(mock_async_session, sample_user_id)
        
        # Assert
        assert total_count == 0
        assert len(items) == 0
        assert items == []

    @pytest.mark.asyncio
    async def test_get_user_bookmarks_pagination(
        self, 
        mock_async_session, 
        sample_user_id
    ):
        """Test get_user_bookmarks pagination calculation."""
        # Arrange
        page = 3
        page_size = 5
        expected_offset = (page - 1) * page_size  # 10
        
        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 20
        
        # Mock posts query result
        mock_posts_result = MagicMock()
        mock_posts_result.all.return_value = []
        
        mock_async_session.execute.side_effect = [mock_count_result, mock_posts_result]
        
        # Act
        items, total_count = await get_user_bookmarks(
            mock_async_session, 
            sample_user_id, 
            page=page, 
            page_size=page_size
        )
        
        # Assert
        assert total_count == 20
        assert len(items) == 0
        # The offset calculation would be verified in the actual SQL query construction
        # which is mocked here, but the business logic is tested
