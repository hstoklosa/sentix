import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import InvalidCredentialsException
from app.services.user import authenticate_user, create_user
from app.schemas.user import UserCreate

pytestmark = pytest.mark.asyncio

async def test_authenticate_user_success(session: AsyncSession):
    # Create test user
    user_data = UserCreate(
        email="test@example.com",
        password="testpassword123",
        is_superuser=False
    )
    await create_user(session=session, user=user_data)
    
    # Authenticate user
    user = await authenticate_user(
        session=session,
        email="test@example.com",
        password="testpassword123"
    )
    
    assert user is not None
    assert user.email == "test@example.com"
    assert not user.is_superuser

async def test_authenticate_user_invalid_email(session: AsyncSession):
    with pytest.raises(InvalidCredentialsException):
        await authenticate_user(
            session=session,
            email="nonexistent@example.com",
            password="testpassword123"
        )

async def test_authenticate_user_invalid_password(session: AsyncSession):
    # Create test user
    user_data = UserCreate(
        email="test@example.com",
        password="testpassword123",
        is_superuser=False
    )
    await create_user(session=session, user=user_data)
    
    with pytest.raises(InvalidCredentialsException):
        await authenticate_user(
            session=session,
            email="test@example.com",
            password="wrongpassword123"
        )

async def test_authenticate_user_password_check(session: AsyncSession):
    # Create test user
    user_data = UserCreate(
        email="test@example.com",
        password="testpassword123",
        is_superuser=False
    )
    created_user = await create_user(session=session, user=user_data)
    
    # Verify password is hashed
    assert created_user.password != "testpassword123"
    
    # Authenticate and verify it works with original password
    user = await authenticate_user(
        session=session,
        email="test@example.com",
        password="testpassword123"
    )
    assert user.id == created_user.id
