import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocket, status

from app.deps_ws import (
    get_token_from_query,
    verify_ws_token,
    get_current_ws_user,
    authenticate_ws_connection
)
from app.core.security import create_access_token
from app.models.user import User


def get_user_id(user: User) -> int:
    """Helper function to get user ID with type safety."""
    assert user.id is not None
    return user.id


class TestWebSocketTokenExtraction:
    """Test WebSocket token extraction functionality."""
    
    @pytest.mark.asyncio
    async def test_get_token_from_query_success(self, mock_settings):
        """Test successful token extraction from query parameters."""
        # Mock WebSocket with query parameters
        mock_websocket = MagicMock()
        mock_websocket.scope = {"query_string": b"token=test-token-123"}
        
        token = await get_token_from_query(mock_websocket)
        
        assert token == "test-token-123"
    
    @pytest.mark.asyncio
    async def test_get_token_from_query_missing(self, mock_settings):
        """Test token extraction when token is missing."""
        # Mock WebSocket without token parameter
        mock_websocket = MagicMock()
        mock_websocket.scope = {"query_string": b""}
        
        token = await get_token_from_query(mock_websocket)
        
        assert token is None
    
    @pytest.mark.asyncio
    async def test_get_token_from_query_empty(self, mock_settings):
        """Test token extraction when token is empty."""
        # Mock WebSocket with empty token parameter
        mock_websocket = MagicMock()
        mock_websocket.scope = {"query_string": b"token="}
        
        token = await get_token_from_query(mock_websocket)
        
        assert token == ""


class TestWebSocketTokenVerification:
    """Test WebSocket token verification functionality."""
    
    @pytest.mark.asyncio
    async def test_verify_ws_token_success(self, test_user: User, mock_settings):
        """Test successful WebSocket token verification."""
        # Create valid token
        valid_token = create_access_token(get_user_id(test_user))
        
        # Mock WebSocket with valid token
        mock_websocket = MagicMock()
        mock_websocket.query_params = {"token": valid_token}
        
        with patch('app.deps_ws.get_token_from_query', return_value=valid_token):
            is_valid, payload = await verify_ws_token(mock_websocket)
        
        assert is_valid is True
        assert payload is not None
        assert payload["type"] == "access"
        assert payload["sub"] == str(test_user.id)
    
    @pytest.mark.asyncio
    async def test_verify_ws_token_invalid(self, mock_settings):
        """Test WebSocket token verification with invalid token."""
        # Mock WebSocket with invalid token
        mock_websocket = MagicMock()
        
        with patch('app.deps_ws.get_token_from_query', return_value="invalid-token"):
            is_valid, payload = await verify_ws_token(mock_websocket)
        
        assert is_valid is False
        assert payload is None
    
    @pytest.mark.asyncio
    async def test_verify_ws_token_missing(self, mock_settings):
        """Test WebSocket token verification when token is missing."""
        # Mock WebSocket without token
        mock_websocket = MagicMock()
        
        with patch('app.deps_ws.get_token_from_query', return_value=None):
            is_valid, payload = await verify_ws_token(mock_websocket)
        
        assert is_valid is False
        assert payload is None


class TestWebSocketUserExtraction:
    """Test WebSocket user extraction functionality."""
    
    @pytest.mark.asyncio
    async def test_get_current_ws_user_success(self, test_user: User, mock_settings):
        """Test successful WebSocket user extraction."""
        # Create valid token
        valid_token = create_access_token(get_user_id(test_user))
        
        # Mock WebSocket
        mock_websocket = MagicMock()
        
        # Mock successful token verification
        with patch('app.deps_ws.verify_ws_token', return_value=(True, {"sub": str(test_user.id)})):
            with patch('app.deps_ws.get_user_by_id', return_value=test_user):
                user = await get_current_ws_user(mock_websocket)
        
        assert user is not None
        assert user.id == test_user.id
    
    @pytest.mark.asyncio
    async def test_get_current_ws_user_invalid_token(self, mock_settings):
        """Test WebSocket user extraction with invalid token."""
        # Mock WebSocket
        mock_websocket = MagicMock()
        
        # Mock failed token verification
        with patch('app.deps_ws.verify_ws_token', return_value=(False, None)):
            user = await get_current_ws_user(mock_websocket)
        
        assert user is None


class TestWebSocketAuthentication:
    """Test WebSocket authentication functionality."""
    
    @pytest.mark.asyncio
    async def test_authenticate_ws_connection_success(self, test_user: User, mock_settings):
        """Test successful WebSocket authentication."""
        # Mock WebSocket
        mock_websocket = MagicMock()
        
        # Mock successful user extraction
        with patch('app.deps_ws.get_current_ws_user', return_value=test_user):
            is_authenticated, user = await authenticate_ws_connection(mock_websocket)
        
        assert is_authenticated is True
        assert user is not None
        assert user.id == test_user.id
    
    @pytest.mark.asyncio
    async def test_authenticate_ws_connection_failure(self, mock_settings):
        """Test failed WebSocket authentication."""
        # Mock WebSocket with async close method
        mock_websocket = MagicMock()
        mock_websocket.close = AsyncMock()
        
        # Mock failed user extraction
        with patch('app.deps_ws.get_current_ws_user', return_value=None):
            is_authenticated, user = await authenticate_ws_connection(mock_websocket)
        
        assert is_authenticated is False
        assert user is None
        mock_websocket.close.assert_called_once_with(code=status.WS_1008_POLICY_VIOLATION)


class TestWebSocketIntegration:
    """Test WebSocket integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_websocket_authentication_flow(self, test_user: User, mock_settings):
        """Test complete WebSocket authentication flow."""
        # Create valid token
        valid_token = create_access_token(get_user_id(test_user))
        
        # Mock WebSocket with token in query
        mock_websocket = MagicMock()
        mock_websocket.scope = {"query_string": f"token={valid_token}".encode()}
        
        # Mock database session and user lookup
        with patch('app.deps_ws.sessionmanager.session') as mock_session:
            mock_session.return_value.__aenter__.return_value = MagicMock()
            with patch('app.deps_ws.get_user_by_id', return_value=test_user):
                is_authenticated, user = await authenticate_ws_connection(mock_websocket)
        
        assert is_authenticated is True
        assert user is not None
        assert user.id == test_user.id
    
    @pytest.mark.asyncio
    async def test_websocket_authentication_with_expired_token(self, test_user: User, mock_settings):
        """Test WebSocket authentication with expired token."""
        # Create expired token
        with patch('app.core.security.datetime') as mock_dt:
            from datetime import datetime, timedelta, timezone
            mock_dt.now.return_value = datetime.now(timezone.utc) - timedelta(hours=1)
            expired_token = create_access_token(get_user_id(test_user))
        
        # Mock WebSocket with expired token and async close method
        mock_websocket = MagicMock()
        mock_websocket.scope = {"query_string": f"token={expired_token}".encode()}
        mock_websocket.close = AsyncMock()
        
        is_authenticated, user = await authenticate_ws_connection(mock_websocket)
        
        assert is_authenticated is False  # Should be False due to expired token
        assert user is None  # Should be None due to expired token
        mock_websocket.close.assert_called_once_with(code=status.WS_1008_POLICY_VIOLATION)
    
    @pytest.mark.asyncio
    async def test_websocket_connection_handling(self, test_user: User, mock_settings):
        """Test WebSocket connection handling scenarios."""
        # Mock WebSocket with async close method
        mock_websocket = MagicMock()
        mock_websocket.close = AsyncMock()
        
        # Test with valid authentication
        with patch('app.deps_ws.get_current_ws_user', return_value=test_user):
            is_authenticated, user = await authenticate_ws_connection(mock_websocket)
            
            assert is_authenticated is True
            assert user == test_user
        
        # Test with invalid authentication
        with patch('app.deps_ws.get_current_ws_user', return_value=None):
            is_authenticated, user = await authenticate_ws_connection(mock_websocket)
            
            assert is_authenticated is False  # Should be False for invalid auth
            assert user is None
            mock_websocket.close.assert_called_once_with(code=status.WS_1008_POLICY_VIOLATION)
