import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.user import User
from app.core.security import verify_password, decode_token, verify_token_type
from app.services.user import create_user
from app.schemas.user import UserCreate

pytestmark = pytest.mark.asyncio

async def test_register_success(client: AsyncClient, session: AsyncSession):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
            "is_superuser": False
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    
    # Check refresh token cookie
    cookies = response.cookies
    assert "refresh_token" in cookies
    refresh_token = cookies["refresh_token"]
    
    # Verify refresh token is valid
    payload = decode_token(refresh_token)
    verify_token_type(payload, "refresh")

async def test_login_success(client: AsyncClient, session: AsyncSession):
    # Create test user
    user_data = UserCreate(
        email="test@example.com",
        password="testpassword123",
        is_superuser=False
    )
    user = await create_user(session=session, user=user_data)
    
    # Attempt login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    
    # Check refresh token cookie
    cookies = response.cookies
    assert "refresh_token" in cookies
    refresh_token = cookies["refresh_token"]
    
    # Verify refresh token is valid
    payload = decode_token(refresh_token)
    verify_token_type(payload, "refresh")

async def test_refresh_token_success(client: AsyncClient, session: AsyncSession):
    # First login to get a refresh token
    user_data = UserCreate(
        email="test@example.com",
        password="testpassword123",
        is_superuser=False
    )
    user = await create_user(session=session, user=user_data)
    
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    
    # Use the refresh token to get a new access token
    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        cookies=login_response.cookies  # Pass the refresh token cookie
    )
    
    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert "access_token" in data
    
    # Verify we got a new refresh token cookie
    cookies = refresh_response.cookies
    assert "refresh_token" in cookies
    new_refresh_token = cookies["refresh_token"]
    assert new_refresh_token != login_response.cookies["refresh_token"]

async def test_refresh_token_missing(client: AsyncClient):
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token missing"

async def test_logout_success(client: AsyncClient):
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out"
    
    # Verify refresh token cookie is cleared
    cookie = response.headers.get("set-cookie", "")
    assert "refresh_token" in cookie
    assert "Max-Age=0" in cookie or "expires" in cookie.lower()

async def test_login_invalid_email(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "testpassword123"
        }
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid email or password"

async def test_login_invalid_password(client: AsyncClient, session: AsyncSession):
    # Create test user
    user_data = UserCreate(
        email="test@example.com",
        password="testpassword123",
        is_superuser=False
    )
    user = await create_user(session=session, user=user_data)
    
    # Attempt login with wrong password
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword123"
        }
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid email or password"

async def test_login_missing_fields(client: AsyncClient):
    # Test missing email
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "password": "testpassword123"
        }
    )
    assert response.status_code == 422

    # Test missing password
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com"
        }
    )
    assert response.status_code == 422

async def test_login_invalid_email_format(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "invalid-email",
            "password": "testpassword123"
        }
    )
    
    assert response.status_code == 422
