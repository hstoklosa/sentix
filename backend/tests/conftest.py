import pytest
import pytest_asyncio
import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator
from unittest.mock import patch

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

from app.core.config import settings
from app.core.database import get_db_session
from app.core.security import create_access_token, create_refresh_token, get_password_hash
from app.models.user import User
from app.models.token import Token
from app.models.bookmark import NewsBookmark
from app.models.news import NewsItem
from app.models.coin import Coin
from app.schemas.user import UserCreate


# Test database URL for SQLite in-memory database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create a connection for the test
    async with test_engine.connect() as conn:
        # Start a transaction
        trans = await conn.begin()
        
        # Create a session bound to this connection
        session = AsyncSession(bind=conn)
        
        try:
            yield session
        finally:
            # Close the session
            await session.close()
            # Rollback the transaction  
            await trans.rollback()


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch('app.core.config.settings') as mock:
        mock.SECRET_KEY = "test-secret-key-for-testing-only"
        mock.ALGORITHM = "HS256"
        mock.ACCESS_TOKEN_EXPIRE_MINUTES = 15
        mock.REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
        mock.ENVIRONMENT = "testing"
        yield mock


@pytest.fixture
def test_user_data():
    """Test user data for creating users."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    return {
        "username": f"testuser_{unique_id}",
        "email": f"test_{unique_id}@example.com",
        "password": "TestPass123!",
        "is_superuser": False
    }


@pytest.fixture  
def test_superuser_data():
    """Test superuser data."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    return {
        "username": f"admin_{unique_id}",
        "email": f"admin_{unique_id}@example.com", 
        "password": "AdminPass123!",
        "is_superuser": True
    }


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_user_data: dict) -> User:
    """Create a test user in the database."""
    user = User(
        username=test_user_data["username"],
        email=test_user_data["email"],
        password=get_password_hash(test_user_data["password"]),
        is_superuser=test_user_data["is_superuser"]
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_superuser(db_session: AsyncSession, test_superuser_data: dict) -> User:
    """Create a test superuser in the database."""
    user = User(
        username=test_superuser_data["username"],
        email=test_superuser_data["email"],
        password=get_password_hash(test_superuser_data["password"]),
        is_superuser=test_superuser_data["is_superuser"]
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def valid_access_token(test_user: User) -> str:
    """Generate a valid access token for testing."""
    assert test_user.id is not None
    return create_access_token(test_user.id)


@pytest.fixture
def valid_refresh_token(test_user: User) -> str:
    """Generate a valid refresh token for testing."""
    assert test_user.id is not None
    return create_refresh_token(test_user.id)


@pytest.fixture
def expired_access_token(test_user: User) -> str:
    """Generate an expired access token for testing."""
    with patch('app.core.security.datetime') as mock_dt:
        # Set expiration to 1 minute ago
        mock_dt.now.return_value = datetime.now() - timedelta(minutes=1)
        assert test_user.id is not None
        return create_access_token(test_user.id)


@pytest.fixture
def expired_refresh_token(test_user: User) -> str:
    """Generate an expired refresh token for testing."""
    with patch('app.core.security.datetime') as mock_dt:
        # Set expiration to 1 day ago
        mock_dt.now.return_value = datetime.now() - timedelta(days=1)
        assert test_user.id is not None
        return create_refresh_token(test_user.id)


@pytest_asyncio.fixture
async def blacklisted_token(db_session: AsyncSession, valid_refresh_token: str) -> Token:
    """Create a blacklisted token in the database."""
    from app.core.security import decode_token
    
    payload = decode_token(valid_refresh_token)
    assert payload is not None
    token = Token(
        jti=payload["jti"],
        expires_at=datetime.fromtimestamp(payload["exp"]),
        is_blacklisted=True
    )
    db_session.add(token)
    await db_session.commit()
    await db_session.refresh(token)
    return token


@pytest.fixture
def mock_time():
    """Mock datetime for consistent testing."""
    with patch('app.core.security.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2025, 7, 15, 12, 0, 0)
        yield mock_dt


# Test data constants
VALID_PASSWORDS = [
    "Password123!",
    "MyStr0ng@Pass",
    "Complex1$Password",
    "Another@Pass1",
    "Secure123#Pass"
]

INVALID_PASSWORDS = [
    ("short", "Password must be at least 8 characters long"),
    ("password123!", "Password must contain at least one uppercase letter"),
    ("PASSWORD123!", "Password must contain at least one lowercase letter"),
    ("PasswordABC!", "Password must contain at least one number"),
    ("Password123", "Password must contain at least one special character!!"),
    ("", "Password must be at least 8 characters long"),
]

VALID_SUBJECTS = [1, "123", 999, "user123"]
INVALID_SUBJECTS = [None, "", "abc", 0, -1]
TOKEN_TYPES = ["access", "refresh"]
