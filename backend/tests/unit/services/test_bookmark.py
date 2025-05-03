import pytest
from fastapi import HTTPException
from sqlmodel import Session
from datetime import datetime
from app.services.bookmark import (
    create_bookmark,
    delete_bookmark,
    is_bookmarked,
    get_user_bookmarks
)
from app.models.bookmark import NewsBookmark
from app.models.news import NewsItem
from app.models.user import User

class TestBookmarkService:
    """Unit tests for the bookmark service module"""
    
    async def test_create_bookmark(self, db_session: Session, user_factory):
        """Test creating a bookmark for a news item"""
        # Arrange
        # Create a user
        from app.services.user import create_user
        user_data = user_factory(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!"
        )
        user = create_user(session=db_session, user=user_data)
        
        # Create a news item
        news_item = NewsItem(
            title="Test News",
            body="This is a test news article",
            url="https://example.com/news/1",
            source="TestSource",
            item_type="article",
            time=datetime.utcnow(),
            sentiment="neutral",
            score=0.5
        )
        db_session.add(news_item)
        db_session.commit()
        db_session.refresh(news_item)
        
        # Act
        bookmark = await create_bookmark(
            session=db_session,
            user_id=user.id,
            news_item_id=news_item.id
        )
        
        # Assert
        assert bookmark is not None
        assert bookmark.user_id == user.id
        assert bookmark.news_item_id == news_item.id
    
    async def test_create_bookmark_nonexistent_news(self, db_session: Session, user_factory):
        """Test creating a bookmark for a nonexistent news item raises an error"""
        # Arrange
        # Create a user
        from app.services.user import create_user
        user_data = user_factory(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!"
        )
        user = create_user(session=db_session, user=user_data)
        
        # Act and Assert
        with pytest.raises(HTTPException) as exc_info:
            await create_bookmark(
                session=db_session,
                user_id=user.id,
                news_item_id=9999  # Nonexistent news item ID
            )
        
        assert exc_info.value.status_code == 404
        assert "News item not found" in str(exc_info.value.detail)
    
    async def test_create_bookmark_duplicate(self, db_session: Session, user_factory):
        """Test creating a duplicate bookmark returns the existing bookmark"""
        # Arrange
        # Create a user
        from app.services.user import create_user
        user_data = user_factory(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!"
        )
        user = create_user(session=db_session, user=user_data)
        
        # Create a news item
        news_item = NewsItem(
            title="Test News",
            body="This is a test news article",
            url="https://example.com/news/2",
            source="TestSource",
            item_type="article",
            time=datetime.utcnow(),
            sentiment="neutral",
            score=0.5
        )
        db_session.add(news_item)
        db_session.commit()
        db_session.refresh(news_item)
        
        # Create the first bookmark
        original_bookmark = await create_bookmark(
            session=db_session,
            user_id=user.id,
            news_item_id=news_item.id
        )
        
        # Act - Try to create a duplicate bookmark
        duplicate_bookmark = await create_bookmark(
            session=db_session,
            user_id=user.id,
            news_item_id=news_item.id
        )
        
        # Assert
        assert duplicate_bookmark is not None
        assert duplicate_bookmark.id == original_bookmark.id  # Should return the existing bookmark
    
    async def test_delete_bookmark(self, db_session: Session, user_factory):
        """Test deleting a bookmark"""
        # Arrange
        # Create a user
        from app.services.user import create_user
        user_data = user_factory(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!"
        )
        user = create_user(session=db_session, user=user_data)
        
        # Create a news item
        news_item = NewsItem(
            title="Test News",
            body="This is a test news article",
            url="https://example.com/news/3",
            source="TestSource",
            item_type="article",
            time=datetime.utcnow(),
            sentiment="neutral",
            score=0.5
        )
        db_session.add(news_item)
        db_session.commit()
        db_session.refresh(news_item)
        
        # Create a bookmark
        await create_bookmark(
            session=db_session,
            user_id=user.id,
            news_item_id=news_item.id
        )
        
        # Act
        result = await delete_bookmark(
            session=db_session,
            user_id=user.id,
            news_item_id=news_item.id
        )
        
        # Assert
        assert result is True
        
        # Verify the bookmark was actually deleted
        bookmark_exists = await is_bookmarked(
            session=db_session,
            user_id=user.id,
            news_item_id=news_item.id
        )
        assert bookmark_exists is False
    
    async def test_delete_nonexistent_bookmark(self, db_session: Session, user_factory):
        """Test deleting a nonexistent bookmark returns False"""
        # Arrange
        # Create a user
        from app.services.user import create_user
        user_data = user_factory(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!"
        )
        user = create_user(session=db_session, user=user_data)
        
        # Create a news item
        news_item = NewsItem(
            title="Test News",
            body="This is a test news article",
            url="https://example.com/news/4",
            source="TestSource",
            item_type="article",
            time=datetime.utcnow(),
            sentiment="neutral",
            score=0.5
        )
        db_session.add(news_item)
        db_session.commit()
        db_session.refresh(news_item)
        
        # Act - Try to delete a bookmark that doesn't exist
        result = await delete_bookmark(
            session=db_session,
            user_id=user.id,
            news_item_id=news_item.id
        )
        
        # Assert
        assert result is False
    
    async def test_is_bookmarked_true(self, db_session: Session, user_factory):
        """Test checking if a news item is bookmarked returns True when it is"""
        # Arrange
        # Create a user
        from app.services.user import create_user
        user_data = user_factory(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!"
        )
        user = create_user(session=db_session, user=user_data)
        
        # Create a news item
        news_item = NewsItem(
            title="Test News",
            body="This is a test news article",
            url="https://example.com/news/5",
            source="TestSource",
            item_type="article",
            time=datetime.utcnow(),
            sentiment="neutral",
            score=0.5
        )
        db_session.add(news_item)
        db_session.commit()
        db_session.refresh(news_item)
        
        # Create a bookmark
        await create_bookmark(
            session=db_session,
            user_id=user.id,
            news_item_id=news_item.id
        )
        
        # Act
        result = await is_bookmarked(
            session=db_session,
            user_id=user.id,
            news_item_id=news_item.id
        )
        
        # Assert
        assert result is True
    
    async def test_is_bookmarked_false(self, db_session: Session, user_factory):
        """Test checking if a news item is bookmarked returns False when it's not"""
        # Arrange
        # Create a user
        from app.services.user import create_user
        user_data = user_factory(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!"
        )
        user = create_user(session=db_session, user=user_data)
        
        # Create a news item
        news_item = NewsItem(
            title="Test News",
            body="This is a test news article",
            url="https://example.com/news/6",
            source="TestSource",
            item_type="article",
            time=datetime.utcnow(),
            sentiment="neutral",
            score=0.5
        )
        db_session.add(news_item)
        db_session.commit()
        db_session.refresh(news_item)
        
        # Act - Check without creating a bookmark
        result = await is_bookmarked(
            session=db_session,
            user_id=user.id,
            news_item_id=news_item.id
        )
        
        # Assert
        assert result is False
    
    async def test_get_user_bookmarks_empty(self, db_session: Session, user_factory):
        """Test getting bookmarks for a user with no bookmarks"""
        # Arrange
        # Create a user
        from app.services.user import create_user
        user_data = user_factory(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!"
        )
        user = create_user(session=db_session, user=user_data)
        
        # Act
        bookmarks, total_count = await get_user_bookmarks(
            session=db_session,
            user_id=user.id
        )
        
        # Assert
        assert len(bookmarks) == 0
        assert total_count == 0
    
    async def test_get_user_bookmarks(self, db_session: Session, user_factory):
        """Test getting bookmarks for a user with bookmarks"""
        # Arrange
        # Create a user
        from app.services.user import create_user
        user_data = user_factory(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!"
        )
        user = create_user(session=db_session, user=user_data)
        
        # Create news items
        news_item1 = NewsItem(
            title="Test News 1",
            body="This is test news article 1",
            url="https://example.com/news/7",
            source="TestSource",
            item_type="article",
            time=datetime.utcnow(),
            sentiment="neutral",
            score=0.5
        )
        news_item2 = NewsItem(
            title="Test News 2",
            body="This is test news article 2",
            url="https://example.com/news/8",
            source="TestSource",
            item_type="article",
            time=datetime.utcnow(),
            sentiment="neutral",
            score=0.5
        )
        db_session.add(news_item1)
        db_session.add(news_item2)
        db_session.commit()
        db_session.refresh(news_item1)
        db_session.refresh(news_item2)
        
        # Create bookmarks
        await create_bookmark(
            session=db_session,
            user_id=user.id,
            news_item_id=news_item1.id
        )
        await create_bookmark(
            session=db_session,
            user_id=user.id,
            news_item_id=news_item2.id
        )
        
        # Act
        bookmarks, total_count = await get_user_bookmarks(
            session=db_session,
            user_id=user.id
        )
        
        # Assert
        assert len(bookmarks) == 2
        assert total_count == 2
        
        # Check that the bookmarks contain the expected news items
        bookmark_news_ids = [bookmark.get("id") for bookmark in bookmarks]
        assert news_item1.id in bookmark_news_ids
        assert news_item2.id in bookmark_news_ids
        
        # Check that bookmark fields are present
        for bookmark in bookmarks:
            assert "bookmark_id" in bookmark
            assert "bookmarked_at" in bookmark
    
    async def test_get_user_bookmarks_pagination(self, db_session: Session, user_factory):
        """Test pagination of user bookmarks"""
        # Arrange
        # Create a user
        from app.services.user import create_user
        user_data = user_factory(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!"
        )
        user = create_user(session=db_session, user=user_data)
        
        # Create 5 news items
        news_items = []
        for i in range(5):
            news_item = NewsItem(
                title=f"Test News {i+1}",
                body=f"This is test news article {i+1}",
                url=f"https://example.com/news/{i+10}",
                source="TestSource",
                item_type="article",
                time=datetime.utcnow(),
                sentiment="neutral",
                score=0.5
            )
            db_session.add(news_item)
            news_items.append(news_item)
        
        db_session.commit()
        for item in news_items:
            db_session.refresh(item)
        
        # Create bookmarks for all news items
        for item in news_items:
            await create_bookmark(
                session=db_session,
                user_id=user.id,
                news_item_id=item.id
            )
        
        # Act - Get the first page with 2 items per page
        page1_bookmarks, total_count = await get_user_bookmarks(
            session=db_session,
            user_id=user.id,
            page=1,
            page_size=2
        )
        
        # Get the second page
        page2_bookmarks, _ = await get_user_bookmarks(
            session=db_session,
            user_id=user.id,
            page=2,
            page_size=2
        )
        
        # Assert
        assert len(page1_bookmarks) == 2
        assert len(page2_bookmarks) == 2
        assert total_count == 5
        
        # Check that page 1 and page 2 contain different items
        page1_ids = [bookmark.get("id") for bookmark in page1_bookmarks]
        page2_ids = [bookmark.get("id") for bookmark in page2_bookmarks]
        assert not set(page1_ids).intersection(set(page2_ids)) 