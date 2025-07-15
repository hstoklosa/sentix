import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user import (
    create_user,
    authenticate_user,
    get_user_by_email,
    get_user_by_username
)
from app.schemas.user import UserCreate
from app.models.user import User
from app.core.security import get_password_hash, verify_password


@pytest.mark.unit
class TestUserService:
    """Test user service functions with mocked database operations."""
    
    @pytest.mark.asyncio
    async def test_create_user_password_not_stored_plain_text(self, mock_async_session):
        """Test create_user to verify that password is not stored in plain text."""
        # Arrange
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="TestPass123!",
            is_superuser=False
        )
        
        # Mock the session operations
        mock_async_session.add = MagicMock()
        mock_async_session.commit = AsyncMock()
        mock_async_session.refresh = AsyncMock()
        
        # Create a mock user that would be returned
        mock_user = User(
            id=1,
            username=user_data.username,
            email=user_data.email,
            password=get_password_hash(user_data.password),  # Simulate hashed password
            is_superuser=user_data.is_superuser
        )
        
        # Mock refresh to set the user attributes
        async def mock_refresh(user):
            user.id = 1
        mock_async_session.refresh.side_effect = mock_refresh
        
        # Act
        result_user = await create_user(session=mock_async_session, user=user_data)
        
        # Assert
        assert result_user is not None
        assert result_user.username == user_data.username
        assert result_user.email == user_data.email
        assert result_user.password != user_data.password  # Password should be hashed
        assert result_user.password.startswith("$2b$")  # bcrypt hash prefix
        assert result_user.is_superuser == user_data.is_superuser
        
        # Verify database operations were called
        mock_async_session.add.assert_called_once()
        mock_async_session.commit.assert_called_once()
        mock_async_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_successful_with_email(self, mock_async_session):
        """Test authenticate_user for a successful authentication with email."""
        # Arrange
        email = "test@example.com"
        password = "TestPass123!"
        hashed_password = get_password_hash(password)
        
        mock_user = User(
            id=1,
            username="testuser",
            email=email,
            password=hashed_password,
            is_superuser=False
        )
        
        # Mock the database query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_async_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result_user = await authenticate_user(
            session=mock_async_session,
            email=email,
            password=password
        )
        
        # Assert
        assert result_user is not None
        assert result_user.id == mock_user.id
        assert result_user.email == email
        assert result_user.username == mock_user.username
        
        # Verify database query was called
        mock_async_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_successful_with_username(self, mock_async_session):
        """Test authenticate_user for a successful authentication with username."""
        # Arrange
        username = "testuser"
        password = "TestPass123!"
        hashed_password = get_password_hash(password)
        
        mock_user = User(
            id=1,
            username=username,
            email="test@example.com",
            password=hashed_password,
            is_superuser=False
        )
        
        # Mock the database query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_async_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result_user = await authenticate_user(
            session=mock_async_session,
            username=username,
            password=password
        )
        
        # Assert
        assert result_user is not None
        assert result_user.id == mock_user.id
        assert result_user.username == username
        assert result_user.email == mock_user.email
        
        # Verify database query was called
        mock_async_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_failed_wrong_password(self, mock_async_session):
        """Test authenticate_user for a failed authentication with incorrect password."""
        # Arrange
        email = "test@example.com"
        correct_password = "TestPass123!"
        wrong_password = "WrongPass456!"
        hashed_password = get_password_hash(correct_password)
        
        mock_user = User(
            id=1,
            username="testuser",
            email=email,
            password=hashed_password,
            is_superuser=False
        )
        
        # Mock the database query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_async_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result_user = await authenticate_user(
            session=mock_async_session,
            email=email,
            password=wrong_password
        )
        
        # Assert
        assert result_user is None
        
        # Verify database query was called
        mock_async_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_failed_user_not_found(self, mock_async_session):
        """Test authenticate_user when user doesn't exist."""
        # Arrange
        email = "nonexistent@example.com"
        password = "TestPass123!"
        
        # Mock the database query result - user not found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_async_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result_user = await authenticate_user(
            session=mock_async_session,
            email=email,
            password=password
        )
        
        # Assert
        assert result_user is None
        
        # Verify database query was called
        mock_async_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_email_lookup_priority(self, mock_async_session):
        """Test authenticate_user prioritizes email over username when both are provided."""
        # Arrange
        email = "test@example.com"
        username = "testuser"
        password = "TestPass123!"
        hashed_password = get_password_hash(password)
        
        mock_user = User(
            id=1,
            username=username,
            email=email,
            password=hashed_password,
            is_superuser=False
        )
        
        # Mock the database query result for email lookup
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_async_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result_user = await authenticate_user(
            session=mock_async_session,
            email=email,
            username=username,  # Both provided
            password=password
        )
        
        # Assert
        assert result_user is not None
        assert result_user.email == email
        
        # Verify database query was called once (should use email, not username)
        mock_async_session.execute.assert_called_once()
        
        # Check that the query was for email (contains User.email in the WHERE clause)
        call_args = mock_async_session.execute.call_args[0][0]
        query_str = str(call_args)
        assert "email" in query_str.lower()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_username_lookup_when_no_email(self, mock_async_session):
        """Test authenticate_user uses username lookup when email is not provided."""
        # Arrange
        username = "testuser"
        password = "TestPass123!"
        hashed_password = get_password_hash(password)
        
        mock_user = User(
            id=1,
            username=username,
            email="test@example.com",
            password=hashed_password,
            is_superuser=False
        )
        
        # Mock the database query result for username lookup
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_async_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result_user = await authenticate_user(
            session=mock_async_session,
            username=username,  # Only username provided
            password=password
        )
        
        # Assert
        assert result_user is not None
        assert result_user.username == username
        
        # Verify database query was called
        mock_async_session.execute.assert_called_once()
        
        # Check that the query was for username
        call_args = mock_async_session.execute.call_args[0][0]
        query_str = str(call_args)
        assert "username" in query_str.lower()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_no_credentials_provided(self, mock_async_session):
        """Test authenticate_user when neither email nor username is provided."""
        # Arrange
        password = "TestPass123!"
        
        # Act
        result_user = await authenticate_user(
            session=mock_async_session,
            password=password
        )
        
        # Assert
        assert result_user is None
        
        # Verify no database query was made
        mock_async_session.execute.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_found(self, mock_async_session):
        """Test get_user_by_email when user exists."""
        # Arrange
        email = "test@example.com"
        mock_user = User(
            id=1,
            username="testuser",
            email=email,
            password="hashed_password",
            is_superuser=False
        )
        
        # Mock the database query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_async_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result_user = await get_user_by_email(session=mock_async_session, email=email)
        
        # Assert
        assert result_user is not None
        assert result_user.email == email
        assert result_user.id == mock_user.id
        
        # Verify database query was called
        mock_async_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, mock_async_session):
        """Test get_user_by_email when user doesn't exist."""
        # Arrange
        email = "nonexistent@example.com"
        
        # Mock the database query result - user not found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_async_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result_user = await get_user_by_email(session=mock_async_session, email=email)
        
        # Assert
        assert result_user is None
        
        # Verify database query was called
        mock_async_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_by_username_found(self, mock_async_session):
        """Test get_user_by_username when user exists."""
        # Arrange
        username = "testuser"
        mock_user = User(
            id=1,
            username=username,
            email="test@example.com",
            password="hashed_password",
            is_superuser=False
        )
        
        # Mock the database query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_async_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result_user = await get_user_by_username(session=mock_async_session, username=username)
        
        # Assert
        assert result_user is not None
        assert result_user.username == username
        assert result_user.id == mock_user.id
        
        # Verify database query was called
        mock_async_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_by_username_not_found(self, mock_async_session):
        """Test get_user_by_username when user doesn't exist."""
        # Arrange
        username = "nonexistent"
        
        # Mock the database query result - user not found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_async_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result_user = await get_user_by_username(session=mock_async_session, username=username)
        
        # Assert
        assert result_user is None
        
        # Verify database query was called
        mock_async_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_database_operations_called(self, mock_async_session):
        """Test that create_user calls the correct database operations in order."""
        # Arrange
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="TestPass123!",
            is_superuser=False
        )
        
        # Mock the session operations
        mock_async_session.add = MagicMock()
        mock_async_session.commit = AsyncMock()
        mock_async_session.refresh = AsyncMock()
        
        # Act
        await create_user(session=mock_async_session, user=user_data)
        
        # Assert - verify all database operations were called in the correct order
        mock_async_session.add.assert_called_once()
        mock_async_session.commit.assert_called_once()
        mock_async_session.refresh.assert_called_once()
        
        # Verify the user object passed to add has hashed password
        added_user = mock_async_session.add.call_args[0][0]
        assert isinstance(added_user, User)
        assert added_user.username == user_data.username
        assert added_user.email == user_data.email
        assert added_user.password != user_data.password
        assert added_user.password.startswith("$2b$")
        assert added_user.is_superuser == user_data.is_superuser
    
    @pytest.mark.asyncio
    async def test_authenticate_user_password_verification_logic(self, mock_async_session):
        """Test that authenticate_user uses proper password verification logic."""
        # Arrange
        email = "test@example.com"
        correct_password = "TestPass123!"
        hashed_password = get_password_hash(correct_password)
        
        mock_user = User(
            id=1,
            username="testuser",
            email=email,
            password=hashed_password,
            is_superuser=False
        )
        
        # Mock the database query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_async_session.execute = AsyncMock(return_value=mock_result)
        
        # Test with correct password
        result_user = await authenticate_user(
            session=mock_async_session,
            email=email,
            password=correct_password
        )
        assert result_user is not None
        
        # Reset mock for next test
        mock_async_session.execute.reset_mock()
        mock_async_session.execute = AsyncMock(return_value=mock_result)
        
        # Test with incorrect password
        result_user = await authenticate_user(
            session=mock_async_session,
            email=email,
            password="WrongPassword123!"
        )
        assert result_user is None
        
        # Verify that database was queried in both cases
        assert mock_async_session.execute.call_count == 1
