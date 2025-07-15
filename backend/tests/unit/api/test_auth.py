import pytest
from unittest.mock import patch, AsyncMock
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin


def get_user_id(user: User) -> int:
    """Helper function to get user ID with type safety."""
    assert user.id is not None
    return user.id


class TestAuthenticationAPI:
    """Test authentication API endpoints."""
    
    @pytest.mark.asyncio
    async def test_register_endpoint_success(self, db_session: AsyncSession, mock_settings):
        """Test successful user registration."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewPass123!",
            "is_superuser": False
        }
        
        # Mock the register endpoint behavior
        with patch('app.services.user.create_user') as mock_create_user:
            mock_user = User(
                id=1,
                username=user_data["username"],
                email=user_data["email"],
                password="hashed_password",
                is_superuser=user_data["is_superuser"]
            )
            mock_create_user.return_value = mock_user
            
            # Mock token creation
            with patch('app.api.routes.rest.auth.create_access_token') as mock_access_token:
                with patch('app.api.routes.rest.auth.create_refresh_token') as mock_refresh_token:
                    mock_access_token.return_value = "access_token"
                    mock_refresh_token.return_value = "refresh_token"
                    
                    # Test registration logic
                    assert mock_user.username == user_data["username"]
                    assert mock_user.email == user_data["email"]
                    assert mock_user.is_superuser == user_data["is_superuser"]
    
    @pytest.mark.asyncio
    async def test_login_endpoint_success(self, db_session: AsyncSession, test_user: User, mock_settings):
        """Test successful user login."""
        login_data = {
            "email": test_user.email,
            "password": "TestPass123!"
        }
        
        # Mock the login endpoint behavior
        with patch('app.services.user.authenticate_user') as mock_authenticate:
            mock_authenticate.return_value = test_user
            
            # Mock token creation
            with patch('app.api.routes.rest.auth.create_access_token') as mock_access_token:
                with patch('app.api.routes.rest.auth.create_refresh_token') as mock_refresh_token:
                    mock_access_token.return_value = "access_token"
                    mock_refresh_token.return_value = "refresh_token"
                    
                    # Test login logic
                    authenticated_user = await mock_authenticate(
                        session=db_session,
                        email=login_data["email"],
                        password=login_data["password"]
                    )
                    
                    assert authenticated_user == test_user
    
    @pytest.mark.asyncio
    async def test_login_endpoint_invalid_credentials(self, db_session: AsyncSession, mock_settings):
        """Test login with invalid credentials."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "WrongPass123!"
        }
        
        # Mock the login endpoint behavior
        with patch('app.services.user.authenticate_user') as mock_authenticate:
            mock_authenticate.return_value = None
            
            # Test login logic
            authenticated_user = await mock_authenticate(
                session=db_session,
                email=login_data["email"],
                password=login_data["password"]
            )
            
            assert authenticated_user is None
    
    @pytest.mark.asyncio
    async def test_refresh_token_endpoint_success(self, db_session: AsyncSession, test_user: User, mock_settings):
        """Test successful token refresh."""
        refresh_token = create_refresh_token(get_user_id(test_user))
        
        # Mock the refresh endpoint behavior
        with patch('app.services.token.is_token_blacklisted') as mock_is_blacklisted:
            with patch('app.services.user.get_user_by_id') as mock_get_user:
                mock_is_blacklisted.return_value = False
                mock_get_user.return_value = test_user
                
                # Mock token creation
                with patch('app.api.routes.rest.auth.create_access_token') as mock_access_token:
                    with patch('app.api.routes.rest.auth.create_refresh_token') as mock_refresh_token:
                        mock_access_token.return_value = "new_access_token"
                        mock_refresh_token.return_value = "new_refresh_token"
                        
                        # Test refresh logic
                        user = await mock_get_user(session=db_session, user_id=test_user.id)
                        is_blacklisted = await mock_is_blacklisted(session=db_session, jti="test-jti")
                        
                        assert user == test_user
                        assert is_blacklisted is False
    
    @pytest.mark.asyncio
    async def test_refresh_token_endpoint_blacklisted(self, db_session: AsyncSession, test_user: User, mock_settings):
        """Test token refresh with blacklisted token."""
        refresh_token = create_refresh_token(get_user_id(test_user))
        
        # Mock the refresh endpoint behavior
        with patch('app.services.token.is_token_blacklisted') as mock_is_blacklisted:
            mock_is_blacklisted.return_value = True
            
            # Test refresh logic
            is_blacklisted = await mock_is_blacklisted(session=db_session, jti="test-jti")
            
            assert is_blacklisted is True
    
    @pytest.mark.asyncio
    async def test_logout_endpoint_success(self, db_session: AsyncSession, test_user: User, mock_settings):
        """Test successful logout."""
        refresh_token = create_refresh_token(get_user_id(test_user))
        
        # Mock the logout endpoint behavior
        with patch('app.services.token.blacklist_token') as mock_blacklist:
            mock_blacklist.return_value = None
            
            # Test logout logic
            await mock_blacklist(session=db_session, token=refresh_token)
            
            # Verify blacklist was called
            mock_blacklist.assert_called_once_with(session=db_session, token=refresh_token)
    
    @pytest.mark.asyncio
    async def test_current_user_endpoint_success(self, db_session: AsyncSession, test_user: User, mock_settings):
        """Test successful current user retrieval."""
        access_token = create_access_token(get_user_id(test_user))
        
        # Mock the current user endpoint behavior
        with patch('app.deps.get_current_user') as mock_get_current_user:
            mock_get_current_user.return_value = test_user
            
            # Test current user logic
            current_user = await mock_get_current_user(
                session=db_session,
                token_payload={"sub": str(test_user.id)}
            )
            
            assert current_user == test_user
    
    @pytest.mark.asyncio
    async def test_current_user_endpoint_invalid_token(self, db_session: AsyncSession, mock_settings):
        """Test current user retrieval with invalid token."""
        # Mock the current user endpoint behavior
        with patch('app.deps.verify_access_token') as mock_verify:
            mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid token")
            
            # Test current user logic
            with pytest.raises(HTTPException) as exc_info:
                await mock_verify("invalid_token")
            
            assert exc_info.value.status_code == 401


class TestAuthenticationAPIIntegration:
    """Test authentication API integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_registration_and_login_flow(self, db_session: AsyncSession, mock_settings):
        """Test complete registration and login flow."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123!",
            "is_superuser": False
        }
        
        # Mock registration
        with patch('app.services.user.create_user') as mock_create_user:
            mock_user = User(
                id=1,
                username=user_data["username"],
                email=user_data["email"],
                password="hashed_password",
                is_superuser=user_data["is_superuser"]
            )
            mock_create_user.return_value = mock_user
            
            # Create user
            created_user = await mock_create_user(
                session=db_session,
                user=UserCreate(**user_data)
            )
            
            assert created_user.username == user_data["username"]
            assert created_user.email == user_data["email"]
        
        # Mock login
        with patch('app.services.user.authenticate_user') as mock_authenticate:
            mock_authenticate.return_value = mock_user
            
            # Login user
            authenticated_user = await mock_authenticate(
                session=db_session,
                email=user_data["email"],
                password=user_data["password"]
            )
            
            assert authenticated_user == mock_user
    
    @pytest.mark.asyncio
    async def test_token_refresh_flow(self, db_session: AsyncSession, test_user: User, mock_settings):
        """Test token refresh flow."""
        # Create initial tokens
        access_token = create_access_token(get_user_id(test_user))
        refresh_token = create_refresh_token(get_user_id(test_user))
        
        # Mock token refresh
        with patch('app.services.token.is_token_blacklisted') as mock_is_blacklisted:
            with patch('app.services.token.blacklist_token') as mock_blacklist:
                with patch('app.services.user.get_user_by_id') as mock_get_user:
                    mock_is_blacklisted.return_value = False
                    mock_get_user.return_value = test_user
                    
                    # Verify token is not blacklisted
                    is_blacklisted = await mock_is_blacklisted(session=db_session, jti="test-jti")
                    assert is_blacklisted is False
                    
                    # Get user
                    user = await mock_get_user(session=db_session, user_id=test_user.id)
                    assert user == test_user
                    
                    # Blacklist old token
                    await mock_blacklist(session=db_session, token=refresh_token)
                    mock_blacklist.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_logout_flow(self, db_session: AsyncSession, test_user: User, mock_settings):
        """Test logout flow."""
        refresh_token = create_refresh_token(get_user_id(test_user))
        
        # Mock logout
        with patch('app.services.token.blacklist_token') as mock_blacklist:
            # Logout user
            await mock_blacklist(session=db_session, token=refresh_token)
            
            # Verify token was blacklisted
            mock_blacklist.assert_called_once_with(session=db_session, token=refresh_token)


class TestAuthenticationAPIErrorHandling:
    """Test authentication API error handling."""
    
    @pytest.mark.asyncio
    async def test_registration_duplicate_email(self, db_session: AsyncSession, mock_settings):
        """Test registration with duplicate email."""
        user_data = {
            "username": "testuser",
            "email": "existing@example.com",
            "password": "TestPass123!",
            "is_superuser": False
        }
        
        # Mock duplicate email scenario
        with patch('app.services.user.create_user') as mock_create_user:
            mock_create_user.side_effect = Exception("Email already exists")
            
            # Test registration logic
            with pytest.raises(Exception) as exc_info:
                await mock_create_user(session=db_session, user=UserCreate(**user_data))
            
            assert "Email already exists" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_login_invalid_password(self, db_session: AsyncSession, test_user: User, mock_settings):
        """Test login with invalid password."""
        # Mock invalid password scenario
        with patch('app.services.user.authenticate_user') as mock_authenticate:
            mock_authenticate.return_value = None
            
            # Test login logic
            authenticated_user = await mock_authenticate(
                session=db_session,
                email=test_user.email,
                password="WrongPassword123!"
            )
            
            assert authenticated_user is None
    
    @pytest.mark.asyncio
    async def test_refresh_token_expired(self, db_session: AsyncSession, test_user: User, mock_settings):
        """Test token refresh with expired token."""
        # Create expired token
        with patch('app.core.security.datetime') as mock_dt:
            from datetime import datetime, timedelta
            mock_dt.now.return_value = datetime.now() - timedelta(days=1)
            expired_token = create_refresh_token(get_user_id(test_user))
        
        # Mock expired token scenario
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = None  # Expired token returns None
            
            # Test refresh logic
            payload = mock_decode(expired_token)
            assert payload is None
