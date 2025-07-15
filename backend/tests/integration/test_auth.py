"""
Integration tests for authentication endpoints.

These tests validate the authentication API endpoints by making HTTP requests
and verifying the responses. They use a real test database (in-memory) but 
mock external network calls.
"""
import pytest
from httpx import AsyncClient
from sqlmodel import select

from app.models.user import User
from app.models.token import Token as BlacklistedToken
from app.core.security import decode_token, verify_token_type


@pytest.mark.integration
class TestAuthRegistration:
    """Test user registration endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "NewUser123!",
            "full_name": "New User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Check response structure
        assert "token" in data
        assert "user" in data
        assert "access_token" in data["token"]
        
        # Check user data
        user = data["user"]
        assert user["email"] == user_data["email"]
        assert user["username"] == user_data["username"]
        assert "id" in user
        assert "password" not in user  # Password should not be returned
        
        # Check access token is valid
        access_token = data["token"]["access_token"]
        token_payload = decode_token(access_token)
        assert token_payload is not None
        assert verify_token_type(token_payload, "access")
        assert token_payload["sub"] == str(user["id"])
        
        # Check refresh token cookie is set
        cookies = response.cookies
        assert "refresh_token" in cookies
        refresh_token = cookies["refresh_token"]
        refresh_payload = decode_token(refresh_token)
        assert refresh_payload is not None
        assert verify_token_type(refresh_payload, "refresh")

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with existing email."""
        user_data = {
            "email": test_user.email,  # Use existing email
            "username": "differentuser",
            "password": "NewUser123!",
            "full_name": "Different User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient, test_user: User):
        """Test registration with existing username."""
        user_data = {
            "email": "different@example.com",
            "username": test_user.username,  # Use existing username
            "password": "NewUser123!",
            "full_name": "Different User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_register_invalid_password(self, client: AsyncClient):
        """Test registration with invalid password."""
        user_data = {
            "email": "weakpass@example.com",
            "username": "weakpass",
            "password": "weak",  # This should fail validation
            "full_name": "Weak Pass User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        # Pydantic validation happens before the route logic, so it returns 422
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


@pytest.mark.integration
class TestAuthLogin:
    """Test user login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success_with_email(self, client: AsyncClient, test_user: User, sample_user_data: dict):
        """Test successful login with email."""
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "token" in data
        assert "user" in data
        assert "access_token" in data["token"]
        
        # Check user data
        user = data["user"]
        assert user["email"] == test_user.email
        assert user["username"] == test_user.username
        assert user["id"] == test_user.id
        
        # Check access token is valid
        access_token = data["token"]["access_token"]
        token_payload = decode_token(access_token)
        assert token_payload is not None
        assert verify_token_type(token_payload, "access")
        assert token_payload["sub"] == str(test_user.id)
        
        # Check refresh token cookie is set
        cookies = response.cookies
        assert "refresh_token" in cookies

    @pytest.mark.asyncio
    async def test_login_success_with_username(self, client: AsyncClient, test_user: User, sample_user_data: dict):
        """Test successful login with username."""
        login_data = {
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check user data matches
        user = data["user"]
        assert user["username"] == test_user.username
        assert user["id"] == test_user.id

    @pytest.mark.asyncio
    async def test_login_incorrect_password(self, client: AsyncClient, sample_user_data: dict):
        """Test login with incorrect password."""
        login_data = {
            "email": sample_user_data["email"],
            "password": "WrongPassword123!"
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_nonexistent_email(self, client: AsyncClient):
        """Test login with non-existent email."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_nonexistent_username(self, client: AsyncClient):
        """Test login with non-existent username."""
        login_data = {
            "username": "nonexistentuser",
            "password": "SomePassword123!"
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


@pytest.mark.integration
class TestAuthUserInfo:
    """Test user info and token management endpoints."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, client: AsyncClient, test_user: User, test_user_token: str):
        """Test fetching current user data with valid access token."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        response = await client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test fetching current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = await client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, client: AsyncClient):
        """Test fetching current user without token."""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


@pytest.mark.integration
class TestAuthTokenRefresh:
    """Test token refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, test_user: User, sample_user_data: dict, db_session):
        """Test successful token refresh."""
        # First login to get refresh token
        login_data = {
            "email": test_user.email,
            "password": sample_user_data["password"]  # Use password from fixture
        }
        
        login_response = await client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        # Get refresh token from cookie
        refresh_token = login_response.cookies.get("refresh_token")
        assert refresh_token is not None
        
        # Set the refresh token as a cookie for the refresh request
        client.cookies.set("refresh_token", refresh_token)
        
        response = await client.post("/api/v1/auth/refresh")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "token" in data
        assert "user" in data
        assert "access_token" in data["token"]
        
        # Check new access token is valid
        new_access_token = data["token"]["access_token"]
        token_payload = decode_token(new_access_token)
        assert token_payload is not None
        assert verify_token_type(token_payload, "access")
        assert token_payload["sub"] == str(test_user.id)
        
        # Check new refresh token cookie is set
        new_refresh_token = response.cookies.get("refresh_token")
        assert new_refresh_token is not None
        assert new_refresh_token != refresh_token  # Should be a new token
        
        # Check old refresh token is blacklisted
        old_token_payload = decode_token(refresh_token)
        old_jti = old_token_payload["jti"]
        
        # Query for blacklisted token
        stmt = select(BlacklistedToken).where(BlacklistedToken.jti == old_jti)
        result = await db_session.execute(stmt)
        blacklisted_token = result.scalar_one_or_none()
        assert blacklisted_token is not None

    @pytest.mark.asyncio
    async def test_refresh_token_missing(self, client: AsyncClient):
        """Test token refresh without refresh token cookie."""
        response = await client.post("/api/v1/auth/refresh")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test token refresh with invalid refresh token."""
        client.cookies.set("refresh_token", "invalid_token")
        
        response = await client.post("/api/v1/auth/refresh")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_refresh_token_blacklisted(self, client: AsyncClient, test_user: User, sample_user_data: dict, db_session):
        """Test token refresh with blacklisted token."""
        # First login and logout to blacklist the refresh token
        login_data = {
            "email": test_user.email,
            "password": sample_user_data["password"]
        }
        
        login_response = await client.post("/api/v1/auth/login", json=login_data)
        refresh_token = login_response.cookies.get("refresh_token")
        
        # Logout to blacklist the token
        client.cookies.set("refresh_token", refresh_token)
        await client.post("/api/v1/auth/logout")
        
        # Try to use the blacklisted token
        response = await client.post("/api/v1/auth/refresh")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


@pytest.mark.integration
class TestAuthLogout:
    """Test user logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_success(self, client: AsyncClient, test_user: User, sample_user_data: dict, db_session):
        """Test successful logout."""
        # First login to get refresh token
        login_data = {
            "email": test_user.email,
            "password": sample_user_data["password"]
        }
        
        login_response = await client.post("/api/v1/auth/login", json=login_data)
        refresh_token = login_response.cookies.get("refresh_token")
        assert refresh_token is not None
        
        # Set the refresh token as a cookie for logout
        client.cookies.set("refresh_token", refresh_token)
        
        response = await client.post("/api/v1/auth/logout")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"
        
        # Check refresh token cookie is deleted
        cookies = response.cookies
        refresh_cookie = cookies.get("refresh_token")
        # Cookie should be deleted (empty value with max_age=0 or similar)
        assert refresh_cookie == "" or refresh_cookie is None
        
        # Check token is blacklisted
        token_payload = decode_token(refresh_token)
        jti = token_payload["jti"]
        
        stmt = select(BlacklistedToken).where(BlacklistedToken.jti == jti)
        result = await db_session.execute(stmt)
        blacklisted_token = result.scalar_one_or_none()
        assert blacklisted_token is not None

    @pytest.mark.asyncio
    async def test_logout_without_token(self, client: AsyncClient):
        """Test logout without refresh token."""
        response = await client.post("/api/v1/auth/logout")
        
        # Should still succeed even without token
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"

    @pytest.mark.asyncio
    async def test_logout_with_invalid_token(self, client: AsyncClient):
        """Test logout with invalid refresh token."""
        client.cookies.set("refresh_token", "invalid_token")
        
        response = await client.post("/api/v1/auth/logout")
        
        # Should still succeed even with invalid token
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"
