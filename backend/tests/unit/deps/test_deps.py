import pytest
from unittest.mock import patch
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import (
    verify_access_token,
    verify_refresh_token,
    get_current_user
)
from app.core.security import create_access_token, create_refresh_token
from app.core.exceptions import InvalidTokenException
from app.models.user import User


def get_user_id(user: User) -> int:
    """Helper function to get user ID with type safety."""
    assert user.id is not None
    return user.id


class TestAccessTokenVerification:
    """Test access token verification functionality."""
    
    @pytest.mark.asyncio
    async def test_verify_valid_access_token(self, test_user: User, mock_settings):
        """Test verification of valid access token."""
        token = create_access_token(get_user_id(test_user))
        
        payload = await verify_access_token(token)
        
        assert payload is not None
        assert payload["type"] == "access"
        assert payload["sub"] == str(test_user.id)
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
    
    @pytest.mark.asyncio
    async def test_verify_expired_access_token(self, test_user: User, mock_settings):
        """Test verification of expired access token."""
        # Create expired token
        with patch('app.core.security.datetime') as mock_dt:
            from datetime import datetime, timedelta, timezone
            # Mock both now() and now(timezone.utc) calls
            mock_dt.now.return_value = datetime.now(timezone.utc) - timedelta(hours=1)
            expired_token = create_access_token(get_user_id(test_user))
        
        with pytest.raises(InvalidTokenException):
            await verify_access_token(expired_token)
    
    @pytest.mark.asyncio
    async def test_verify_invalid_access_token(self, mock_settings):
        """Test verification of invalid access token."""
        invalid_token = "invalid.token.string"
        
        with pytest.raises(InvalidTokenException):
            await verify_access_token(invalid_token)


class TestRefreshTokenVerification:
    """Test refresh token verification functionality."""
    
    @pytest.mark.asyncio
    async def test_verify_valid_refresh_token(self, db_session: AsyncSession, test_user: User, mock_settings):
        """Test verification of valid refresh token."""
        refresh_token = create_refresh_token(get_user_id(test_user))
        
        payload = await verify_refresh_token(db_session, refresh_token)
        
        assert payload is not None
        assert payload["type"] == "refresh"
        assert payload["sub"] == str(test_user.id)
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
    
    @pytest.mark.asyncio
    async def test_verify_missing_refresh_token(self, db_session: AsyncSession, mock_settings):
        """Test verification when refresh token is missing."""
        with pytest.raises(InvalidTokenException):
            await verify_refresh_token(db_session, None)
    
    @pytest.mark.asyncio
    async def test_verify_blacklisted_refresh_token(self, db_session: AsyncSession, test_user: User, mock_settings):
        """Test verification of blacklisted refresh token."""
        from app.services.token import blacklist_token
        
        refresh_token = create_refresh_token(get_user_id(test_user))
        
        # Blacklist the token
        await blacklist_token(session=db_session, token=refresh_token)
        
        with pytest.raises(InvalidTokenException):
            await verify_refresh_token(db_session, refresh_token)


class TestCurrentUserExtraction:
    """Test current user extraction functionality."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, db_session: AsyncSession, test_user: User, mock_settings):
        """Test successful current user extraction."""
        token = create_access_token(get_user_id(test_user))
        payload = await verify_access_token(token)
        
        current_user = await get_current_user(db_session, payload)
        
        assert current_user is not None
        assert current_user.id == test_user.id
        assert current_user.email == test_user.email
        assert current_user.username == test_user.username
        assert current_user.is_superuser == test_user.is_superuser
    
    @pytest.mark.asyncio
    async def test_get_current_user_nonexistent_user(self, db_session: AsyncSession, mock_settings):
        """Test current user extraction with non-existent user."""
        # Create payload with non-existent user ID
        payload = {
            "type": "access",
            "sub": "99999",  # Non-existent user ID
            "exp": 1234567890,
            "iat": 1234567890,
            "jti": "test-jti"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db_session, payload)
        
        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_current_user_missing_subject(self, db_session: AsyncSession, mock_settings):
        """Test current user extraction with missing subject."""
        payload = {
            "type": "access",
            "exp": 1234567890,
            "iat": 1234567890,
            "jti": "test-jti"
            # Missing "sub" field
        }
        
        with pytest.raises(InvalidTokenException):
            await get_current_user(db_session, payload)
    
    @pytest.mark.asyncio
    async def test_get_current_superuser(self, db_session: AsyncSession, test_superuser: User, mock_settings):
        """Test current user extraction for superuser."""
        token = create_access_token(get_user_id(test_superuser))
        payload = await verify_access_token(token)
        
        current_user = await get_current_user(db_session, payload)
        
        assert current_user is not None
        assert current_user.id == test_superuser.id
        assert current_user.is_superuser is True


class TestDependenciesIntegration:
    """Test integration of dependencies."""
    
    @pytest.mark.asyncio
    async def test_full_authentication_flow(self, db_session: AsyncSession, test_user: User, mock_settings):
        """Test complete authentication flow."""
        # Create access token
        access_token = create_access_token(get_user_id(test_user))
        
        # Verify access token
        payload = await verify_access_token(access_token)
        
        # Get current user
        current_user = await get_current_user(db_session, payload)
        
        # Verify complete flow
        assert current_user.id == test_user.id
        assert current_user.email == test_user.email
        assert current_user.username == test_user.username
    
    @pytest.mark.asyncio
    async def test_refresh_token_flow(self, db_session: AsyncSession, test_user: User, mock_settings):
        """Test refresh token verification flow."""
        # Create refresh token
        refresh_token = create_refresh_token(get_user_id(test_user))
        
        # Verify refresh token
        payload = await verify_refresh_token(db_session, refresh_token)
        
        # Verify payload structure
        assert payload["type"] == "refresh"
        assert payload["sub"] == str(test_user.id)
        assert "jti" in payload
