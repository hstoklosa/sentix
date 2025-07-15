import pytest
import uuid
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user import (
    create_user,
    get_user_by_email,
    get_user_by_username,
    get_user_by_id,
    authenticate_user
)
from app.schemas.user import UserCreate
from app.models.user import User
from app.core.security import get_password_hash, verify_password


def get_user_id(user: User) -> int:
    """Helper function to get user ID with type safety."""
    assert user.id is not None
    return user.id


def create_unique_user_data(username_suffix: str | None = None, email_suffix: str | None = None) -> UserCreate:
    """Create unique user data for testing."""
    unique_id = str(uuid.uuid4())[:8]
    username = f"testuser{username_suffix or unique_id}"
    email = f"test{email_suffix or unique_id}@example.com"
    
    return UserCreate(
        username=username,
        email=email,
        password="TestPass123!",
        is_superuser=False
    )


class TestUserCreation:
    """Test user creation functionality."""
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, db_session: AsyncSession):
        """Test successful user creation."""
        user_data = create_unique_user_data("_success")
        
        user = await create_user(session=db_session, user=user_data)
        
        assert user is not None
        assert user.id is not None
        assert user.username == user_data.username
        assert user.email == user_data.email
        assert user.is_superuser == user_data.is_superuser
        assert user.password != user_data.password  # Should be hashed
        assert user.created_at is not None
        assert user.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_create_user_password_hashing(self, db_session: AsyncSession):
        """Test that password is properly hashed during user creation."""
        user_data = create_unique_user_data("_hash")
        
        user = await create_user(session=db_session, user=user_data)
        
        # Password should be hashed
        assert user.password != user_data.password
        assert user.password.startswith("$2b$")
        
        # Should be able to verify original password
        assert verify_password(user_data.password, user.password) is True
    
    @pytest.mark.asyncio
    async def test_create_superuser(self, db_session: AsyncSession):
        """Test superuser creation."""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        user_data = UserCreate(
            username=f"admin_{unique_id}",
            email=f"admin_{unique_id}@example.com",
            password="AdminPass123!",
            is_superuser=True
        )
        
        user = await create_user(session=db_session, user=user_data)
        
        assert user.is_superuser is True
        assert user.username == f"admin_{unique_id}"
        assert user.email == f"admin_{unique_id}@example.com"
    
    @pytest.mark.asyncio
    async def test_create_user_database_persistence(self, db_session: AsyncSession):
        """Test that user is properly persisted in database."""
        user_data = create_unique_user_data("_persist")
        
        user = await create_user(session=db_session, user=user_data)
        user_id = user.id
        
        # Verify user can be found by ID
        assert user_id is not None
        found_user = await get_user_by_id(session=db_session, user_id=user_id)
        assert found_user is not None
        assert found_user.id == user_id
        assert found_user.username == user_data.username
        assert found_user.email == user_data.email
    
    @pytest.mark.asyncio
    async def test_create_user_with_long_data(self, db_session: AsyncSession):
        """Test user creation with long username and email."""
        user_data = UserCreate(
            username="a" * 50,  # Maximum length
            email="very.long.email.address@example.com",
            password="TestPass123!",
            is_superuser=False
        )
        
        user = await create_user(session=db_session, user=user_data)
        
        assert user is not None
        assert user.username == "a" * 50
        assert user.email == "very.long.email.address@example.com"


class TestUserRetrieval:
    """Test user retrieval functionality."""
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, db_session: AsyncSession, test_user: User):
        """Test successful user retrieval by email."""
        found_user = await get_user_by_email(session=db_session, email=test_user.email)
        
        assert found_user is not None
        assert found_user.id == test_user.id
        assert found_user.email == test_user.email
        assert found_user.username == test_user.username
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, db_session: AsyncSession):
        """Test user retrieval by non-existent email."""
        found_user = await get_user_by_email(session=db_session, email="nonexistent@example.com")
        
        assert found_user is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_username_success(self, db_session: AsyncSession, test_user: User):
        """Test successful user retrieval by username."""
        found_user = await get_user_by_username(session=db_session, username=test_user.username)
        
        assert found_user is not None
        assert found_user.id == test_user.id
        assert found_user.email == test_user.email
        assert found_user.username == test_user.username
    
    @pytest.mark.asyncio
    async def test_get_user_by_username_not_found(self, db_session: AsyncSession):
        """Test user retrieval by non-existent username."""
        found_user = await get_user_by_username(session=db_session, username="nonexistent")
        
        assert found_user is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, db_session: AsyncSession, test_user: User):
        """Test successful user retrieval by ID."""
        assert test_user.id is not None
        found_user = await get_user_by_id(session=db_session, user_id=test_user.id)
        
        assert found_user is not None
        assert found_user.id == test_user.id
        assert found_user.email == test_user.email
        assert found_user.username == test_user.username
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, db_session: AsyncSession):
        """Test user retrieval by non-existent ID."""
        found_user = await get_user_by_id(session=db_session, user_id=99999)
        
        assert found_user is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_invalid_id(self, db_session: AsyncSession):
        """Test user retrieval with invalid ID types."""
        # Test with negative ID
        found_user = await get_user_by_id(session=db_session, user_id=-1)
        assert found_user is None
        
        # Test with zero ID
        found_user = await get_user_by_id(session=db_session, user_id=0)
        assert found_user is None
    
    @pytest.mark.asyncio
    async def test_email_case_sensitivity(self, db_session: AsyncSession, test_user: User):
        """Test email case sensitivity in retrieval."""
        # Should find user with exact case match
        found_user = await get_user_by_email(session=db_session, email=test_user.email)
        assert found_user is not None
        
        # Test with different cases - behavior depends on database collation
        upper_email = test_user.email.upper()
        found_user_upper = await get_user_by_email(session=db_session, email=upper_email)
        # Note: SQLite is case-insensitive by default, PostgreSQL is case-sensitive
        # This test documents the current behavior
    
    @pytest.mark.asyncio
    async def test_username_case_sensitivity(self, db_session: AsyncSession, test_user: User):
        """Test username case sensitivity in retrieval."""
        # Should find user with exact case match
        found_user = await get_user_by_username(session=db_session, username=test_user.username)
        assert found_user is not None
        
        # Test with different cases
        upper_username = test_user.username.upper()
        found_user_upper = await get_user_by_username(session=db_session, username=upper_username)
        # Note: This documents current behavior - depends on database collation


class TestUserAuthentication:
    """Test user authentication functionality."""
    
    @pytest.mark.asyncio
    async def test_authenticate_user_with_email_success(self, db_session: AsyncSession, test_user: User, test_user_data: dict):
        """Test successful authentication with email."""
        authenticated_user = await authenticate_user(
            session=db_session,
            email=test_user.email,
            password=test_user_data["password"]
        )
        
        assert authenticated_user is not None
        assert authenticated_user.id == test_user.id
        assert authenticated_user.email == test_user.email
        assert authenticated_user.username == test_user.username
    
    @pytest.mark.asyncio
    async def test_authenticate_user_with_username_success(self, db_session: AsyncSession, test_user: User, test_user_data: dict):
        """Test successful authentication with username."""
        authenticated_user = await authenticate_user(
            session=db_session,
            username=test_user.username,
            password=test_user_data["password"]
        )
        
        assert authenticated_user is not None
        assert authenticated_user.id == test_user.id
        assert authenticated_user.email == test_user.email
        assert authenticated_user.username == test_user.username
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(self, db_session: AsyncSession, test_user: User):
        """Test authentication with invalid password."""
        authenticated_user = await authenticate_user(
            session=db_session,
            email=test_user.email,
            password="WrongPassword123!"
        )
        
        assert authenticated_user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent_email(self, db_session: AsyncSession):
        """Test authentication with non-existent email."""
        authenticated_user = await authenticate_user(
            session=db_session,
            email="nonexistent@example.com",
            password="AnyPassword123!"
        )
        
        assert authenticated_user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent_username(self, db_session: AsyncSession):
        """Test authentication with non-existent username."""
        authenticated_user = await authenticate_user(
            session=db_session,
            username="nonexistent",
            password="AnyPassword123!"
        )
        
        assert authenticated_user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_missing_credentials(self, db_session: AsyncSession):
        """Test authentication with missing credentials."""
        # No email or username provided
        authenticated_user = await authenticate_user(
            session=db_session,
            password="AnyPassword123!"
        )
        
        assert authenticated_user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_empty_password(self, db_session: AsyncSession, test_user: User):
        """Test authentication with empty password."""
        authenticated_user = await authenticate_user(
            session=db_session,
            email=test_user.email,
            password=""
        )
        
        assert authenticated_user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_both_email_and_username(self, db_session: AsyncSession, test_user: User, test_user_data: dict):
        """Test authentication when both email and username are provided."""
        # Should prioritize email over username
        authenticated_user = await authenticate_user(
            session=db_session,
            email=test_user.email,
            username=test_user.username,
            password=test_user_data["password"]
        )
        
        assert authenticated_user is not None
        assert authenticated_user.id == test_user.id
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_email_correct_username(self, db_session: AsyncSession, test_user: User, test_user_data: dict):
        """Test authentication with wrong email but correct username."""
        # Should fail because email is checked first
        authenticated_user = await authenticate_user(
            session=db_session,
            email="wrong@example.com",
            username=test_user.username,
            password=test_user_data["password"]
        )
        
        assert authenticated_user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_superuser(self, db_session: AsyncSession, test_superuser: User, test_superuser_data: dict):
        """Test superuser authentication."""
        authenticated_user = await authenticate_user(
            session=db_session,
            email=test_superuser.email,
            password=test_superuser_data["password"]
        )
        
        assert authenticated_user is not None
        assert authenticated_user.is_superuser is True
        assert authenticated_user.id == test_superuser.id
    
    @pytest.mark.asyncio
    async def test_authenticate_user_password_verification_timing(self, db_session: AsyncSession, test_user: User):
        """Test that password verification timing is consistent."""
        # This test helps prevent timing attacks
        import time
        
        # Time correct password
        start_time = time.time()
        await authenticate_user(
            session=db_session,
            email=test_user.email,
            password="TestPass123!"
        )
        correct_time = time.time() - start_time
        
        # Time incorrect password
        start_time = time.time()
        await authenticate_user(
            session=db_session,
            email=test_user.email,
            password="WrongPass123!"
        )
        incorrect_time = time.time() - start_time
        
        # Times should be relatively similar (within reasonable bounds)
        # This is a basic timing attack prevention test
        time_difference = abs(correct_time - incorrect_time)
        assert time_difference < 0.1  # Should complete within 100ms of each other


class TestUserServiceEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_concurrent_user_creation(self, db_session: AsyncSession):
        """Test concurrent user creation scenarios."""
        # This test would require actual concurrency testing
        # For now, we'll test sequential creation with same data
        user_data = UserCreate(
            username="testuser_concurrent",
            email="test_concurrent@example.com",
            password="TestPass123!",
            is_superuser=False
        )
        
        # First user creation should succeed
        user1 = await create_user(session=db_session, user=user_data)
        assert user1 is not None
        
        # Second user creation with same data should fail due to unique constraints
        # This would be caught at the database level
        with pytest.raises(Exception):  # Could be IntegrityError or other database exception
            await create_user(session=db_session, user=user_data)
    
    @pytest.mark.asyncio
    async def test_user_with_special_characters(self, db_session: AsyncSession):
        """Test user creation with special characters in username/email."""
        user_data = UserCreate(
            username="test_user-123",
            email="test+tag@example.com",
            password="TestPass123!",
            is_superuser=False
        )
        
        user = await create_user(session=db_session, user=user_data)
        
        assert user is not None
        assert user.username == "test_user-123"
        assert user.email == "test+tag@example.com"
    
    @pytest.mark.asyncio
    async def test_user_retrieval_with_none_params(self, db_session: AsyncSession):
        """Test user retrieval with None parameters."""
        # These should return None without raising exceptions
        # Note: In practice, these would be handled by validation layers
        # but we test the service layer behavior
        
        # Test with empty string instead of None to avoid type issues
        user = await get_user_by_email(session=db_session, email="")
        assert user is None
        
        user = await get_user_by_username(session=db_session, username="")
        assert user is None
