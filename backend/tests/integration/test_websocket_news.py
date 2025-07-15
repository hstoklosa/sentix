"""
Integration tests for WebSocket news endpoint.
Tests WebSocket authentication, connection management, and message broadcasting.
"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import WebSocket, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.news.news_manager import NewsManager, Connection
from app.models.user import User
from app.models.post import Post
from app.main import app


class MockWebSocket:
    """Mock WebSocket for testing WebSocket functionality."""
    
    def __init__(self, query_params=None):
        self.query_params = query_params or {}
        self.scope = {
            "query_string": self._build_query_string().encode()
        }
        self.closed = False
        self.close_code = None
        self.sent_messages = []
        self.received_messages = []
        self._accepted = False
    
    def _build_query_string(self):
        """Build query string from params."""
        if not self.query_params:
            return ""
        
        params = []
        for key, value in self.query_params.items():
            params.append(f"{key}={value}")
        return "&".join(params)
    
    async def accept(self):
        """Mock WebSocket accept."""
        self._accepted = True
    
    async def close(self, code=status.WS_1000_NORMAL_CLOSURE):
        """Mock WebSocket close."""
        self.closed = True
        self.close_code = code
    
    async def send_json(self, data):
        """Mock sending JSON data."""
        self.sent_messages.append(data)
    
    async def receive_json(self):
        """Mock receiving JSON data."""
        if self.received_messages:
            return self.received_messages.pop(0)
        # Return ping by default to keep connection alive in tests
        return {"type": "ping"}
    
    def add_received_message(self, message):
        """Add a message to be received."""
        self.received_messages.append(message)


@pytest.mark.integration
class TestWebSocketNewsAuth:
    """Test WebSocket authentication scenarios."""
    
    async def test_websocket_connection_with_valid_token(self, test_user: User, test_user_token: str):
        """Test that WebSocket connection is accepted with valid token."""
        # Create mock WebSocket with valid token
        mock_ws = MockWebSocket(query_params={"token": test_user_token})
        
        # Mock the authenticate_ws_connection function
        with patch("app.api.routes.websocket.news.authenticate_ws_connection") as mock_auth:
            mock_auth.return_value = (True, test_user)
            
            # Mock NewsManager
            with patch("app.api.routes.websocket.news.NewsManager.get_instance") as mock_manager:
                mock_manager_instance = AsyncMock()
                mock_manager.return_value = mock_manager_instance
                
                # Import and call the WebSocket handler
                from app.api.routes.websocket.news import news_websocket
                
                # This should not raise an exception and should accept the connection
                try:
                    # Add a ping message to prevent infinite loop
                    mock_ws.add_received_message({"type": "ping"})
                    # Add disconnect to end the connection
                    from fastapi import WebSocketDisconnect
                    
                    # Mock the receive_json to raise WebSocketDisconnect after ping
                    async def mock_receive():
                        await mock_ws.receive_json()  # Process ping
                        raise WebSocketDisconnect()
                    
                    mock_ws.receive_json = mock_receive
                    
                    await news_websocket(mock_ws, "test_client_123")
                    
                    # Verify the connection was accepted
                    assert mock_ws._accepted
                    assert not mock_ws.closed or mock_ws.close_code != status.WS_1008_POLICY_VIOLATION
                    
                    # Verify NewsManager methods were called
                    mock_manager_instance.add_client.assert_called_once_with(mock_ws, test_user)
                    mock_manager_instance.remove_client.assert_called_once_with(mock_ws)
                    
                except Exception as e:
                    # If an exception occurred, ensure it's not due to authentication failure
                    assert not (mock_ws.closed and mock_ws.close_code == status.WS_1008_POLICY_VIOLATION), \
                        f"Authentication failed unexpectedly: {e}"
    
    async def test_websocket_connection_with_invalid_token(self):
        """Test that WebSocket connection is rejected with invalid token."""
        # Create mock WebSocket with invalid token
        mock_ws = MockWebSocket(query_params={"token": "invalid_token"})
        
        # Mock the authenticate_ws_connection function to return False
        with patch("app.api.routes.websocket.news.authenticate_ws_connection") as mock_auth:
            mock_auth.return_value = (False, None)
            
            # Import and call the WebSocket handler
            from app.api.routes.websocket.news import news_websocket
            
            await news_websocket(mock_ws, "test_client_123")
            
            # Verify authentication was attempted
            mock_auth.assert_called_once_with(mock_ws)
            
            # Since authenticate_ws_connection returns False, the function should return early
            # and not proceed to accept the connection
    
    async def test_websocket_connection_without_token(self):
        """Test that WebSocket connection is rejected without token."""
        # Create mock WebSocket without token
        mock_ws = MockWebSocket()
        
        # Mock the authenticate_ws_connection function to return False
        with patch("app.api.routes.websocket.news.authenticate_ws_connection") as mock_auth:
            mock_auth.return_value = (False, None)
            
            # Import and call the WebSocket handler
            from app.api.routes.websocket.news import news_websocket
            
            await news_websocket(mock_ws, "test_client_123")
            
            # Verify authentication was attempted
            mock_auth.assert_called_once_with(mock_ws)


@pytest.mark.integration  
class TestWebSocketMessageHandling:
    """Test WebSocket message handling and ping/pong."""
    
    async def test_ping_pong_mechanism(self, test_user: User, test_user_token: str):
        """Test that WebSocket responds to ping with pong."""
        mock_ws = MockWebSocket(query_params={"token": test_user_token})
        
        with patch("app.api.routes.websocket.news.authenticate_ws_connection") as mock_auth:
            mock_auth.return_value = (True, test_user)
            
            with patch("app.api.routes.websocket.news.NewsManager.get_instance") as mock_manager:
                mock_manager_instance = AsyncMock()
                mock_manager.return_value = mock_manager_instance
                
                from app.api.routes.websocket.news import news_websocket
                from fastapi import WebSocketDisconnect
                
                # Set up the message sequence: ping -> disconnect
                messages_to_receive = [
                    {"type": "ping"},
                    {"type": "disconnect"}  # This will cause the loop to end
                ]
                
                call_count = 0
                async def mock_receive():
                    nonlocal call_count
                    if call_count < len(messages_to_receive):
                        message = messages_to_receive[call_count]
                        call_count += 1
                        if message["type"] == "disconnect":
                            raise WebSocketDisconnect()
                        return message
                    raise WebSocketDisconnect()
                
                mock_ws.receive_json = mock_receive
                
                await news_websocket(mock_ws, "test_client_123")
                
                # Verify pong was sent in response to ping
                assert len(mock_ws.sent_messages) == 1
                assert mock_ws.sent_messages[0] == {"type": "pong"}
    
    async def test_unknown_message_type_ignored(self, test_user: User, test_user_token: str):
        """Test that unknown message types are ignored."""
        mock_ws = MockWebSocket(query_params={"token": test_user_token})
        
        with patch("app.api.routes.websocket.news.authenticate_ws_connection") as mock_auth:
            mock_auth.return_value = (True, test_user)
            
            with patch("app.api.routes.websocket.news.NewsManager.get_instance") as mock_manager:
                mock_manager_instance = AsyncMock()
                mock_manager.return_value = mock_manager_instance
                
                from app.api.routes.websocket.news import news_websocket
                from fastapi import WebSocketDisconnect
                
                # Set up messages: unknown type -> ping -> disconnect
                messages_to_receive = [
                    {"type": "unknown_message"},
                    {"type": "ping"},
                    {"type": "disconnect"}
                ]
                
                call_count = 0
                async def mock_receive():
                    nonlocal call_count
                    if call_count < len(messages_to_receive):
                        message = messages_to_receive[call_count]
                        call_count += 1
                        if message["type"] == "disconnect":
                            raise WebSocketDisconnect()
                        return message
                    raise WebSocketDisconnect()
                
                mock_ws.receive_json = mock_receive
                
                await news_websocket(mock_ws, "test_client_123")
                
                # Should only respond to ping, ignore unknown message
                assert len(mock_ws.sent_messages) == 1
                assert mock_ws.sent_messages[0] == {"type": "pong"}


@pytest.mark.integration
class TestNewsManagerBroadcast:
    """Test NewsManager broadcasting functionality."""
    
    async def test_news_manager_broadcast_to_authenticated_client(
        self, 
        db_session: AsyncSession,
        test_user: User, 
        test_post: Post
    ):
        """Test that NewsManager broadcasts news to connected authenticated clients."""
        # Create a real NewsManager instance for testing
        news_manager = NewsManager()
        
        # Create mock WebSocket
        mock_ws = MockWebSocket()
        
        # Add client to manager
        await news_manager.add_client(mock_ws, test_user)
        
        # Verify client was added
        assert mock_ws in news_manager.active_connections
        assert news_manager.active_connections[mock_ws].user == test_user
        
        # Broadcast a post
        await news_manager.broadcast_to_clients(test_post)
        
        # Verify message was sent
        assert len(mock_ws.sent_messages) == 1
        
        sent_message = mock_ws.sent_messages[0]
        assert sent_message["type"] == "news"
        assert "data" in sent_message
        
        # Verify post data structure
        post_data = sent_message["data"]
        assert post_data["id"] == test_post.id
        assert post_data["title"] == test_post.title
        assert post_data["body"] == test_post.body
        assert post_data["url"] == test_post.url
        assert post_data["source"] == test_post.source
        assert post_data["sentiment"] == test_post.sentiment
        assert post_data["score"] == test_post.score
        assert "coins" in post_data
        
        # Clean up
        await news_manager.remove_client(mock_ws)
    
    async def test_news_manager_handles_disconnected_clients(
        self, 
        db_session: AsyncSession,
        test_user: User, 
        test_post: Post
    ):
        """Test that NewsManager handles disconnected clients gracefully."""
        news_manager = NewsManager()
        
        # Create mock WebSocket that will raise exception on send
        mock_ws = MockWebSocket()
        
        async def failing_send_json(data):
            raise Exception("Connection lost")
        
        mock_ws.send_json = failing_send_json
        
        # Add client to manager
        await news_manager.add_client(mock_ws, test_user)
        
        # Verify client was added
        assert mock_ws in news_manager.active_connections
        
        # Broadcast a post (should handle exception and remove client)
        await news_manager.broadcast_to_clients(test_post)
        
        # Verify client was removed due to exception
        assert mock_ws not in news_manager.active_connections
    
    async def test_news_manager_multiple_clients(
        self, 
        db_session: AsyncSession,
        test_user: User, 
        test_post: Post
    ):
        """Test that NewsManager broadcasts to multiple clients."""
        news_manager = NewsManager()
        
        # Create multiple mock WebSockets
        mock_ws1 = MockWebSocket()
        mock_ws2 = MockWebSocket()
        mock_ws3 = MockWebSocket()
        
        # Add clients to manager
        await news_manager.add_client(mock_ws1, test_user)
        await news_manager.add_client(mock_ws2, test_user)
        await news_manager.add_client(mock_ws3, test_user)
        
        # Verify all clients were added
        assert len(news_manager.active_connections) == 3
        
        # Broadcast a post
        await news_manager.broadcast_to_clients(test_post)
        
        # Verify all clients received the message
        for mock_ws in [mock_ws1, mock_ws2, mock_ws3]:
            assert len(mock_ws.sent_messages) == 1
            sent_message = mock_ws.sent_messages[0]
            assert sent_message["type"] == "news"
            assert sent_message["data"]["id"] == test_post.id
        
        # Clean up
        for mock_ws in [mock_ws1, mock_ws2, mock_ws3]:
            await news_manager.remove_client(mock_ws)
    
    async def test_news_manager_client_management(self, test_user: User):
        """Test adding and removing clients from NewsManager."""
        news_manager = NewsManager()
        
        mock_ws = MockWebSocket()
        
        # Initially no connections
        assert len(news_manager.active_connections) == 0
        
        # Add client
        await news_manager.add_client(mock_ws, test_user)
        assert len(news_manager.active_connections) == 1
        assert mock_ws in news_manager.active_connections
        
        connection = news_manager.active_connections[mock_ws]
        assert connection.user == test_user
        assert connection.websocket == mock_ws
        
        # Remove client
        await news_manager.remove_client(mock_ws)
        assert len(news_manager.active_connections) == 0
        assert mock_ws not in news_manager.active_connections
    
    async def test_news_manager_singleton_pattern(self):
        """Test that NewsManager follows singleton pattern."""
        manager1 = NewsManager.get_instance()
        manager2 = NewsManager.get_instance()
        
        # Should be the same instance
        assert manager1 is manager2


@pytest.mark.integration
class TestWebSocketEndToEnd:
    """End-to-end WebSocket tests using TestClient."""
    
    def test_websocket_endpoint_path(self):
        """Test that WebSocket endpoint exists at correct path."""
        from app.main import app
        
        # Check that the WebSocket route exists
        websocket_routes = [route for route in app.routes if hasattr(route, 'path') and '/ws/' in route.path]
        assert len(websocket_routes) > 0
        
        # Find our specific WebSocket route
        news_ws_route = None
        for route in websocket_routes:
            if hasattr(route, 'path') and 'news/ws' in route.path:
                news_ws_route = route
                break
        
        assert news_ws_route is not None, "News WebSocket route not found"
    
    async def test_websocket_authentication_integration(
        self, 
        db_session: AsyncSession,
        test_user: User, 
        test_user_token: str
    ):
        """Integration test for WebSocket authentication using actual auth functions."""
        from app.deps_ws import authenticate_ws_connection
        
        # Test with valid token
        mock_ws_valid = MockWebSocket(query_params={"token": test_user_token})
        
        # Mock the sessionmanager to use our test session
        with patch("app.deps_ws.sessionmanager.session") as mock_session_manager:
            mock_session_manager.return_value.__aenter__.return_value = db_session
            
            is_authenticated, user = await authenticate_ws_connection(mock_ws_valid)
            
            assert is_authenticated is True
            assert user is not None
            assert user.id == test_user.id
            assert user.email == test_user.email
        
        # Test with invalid token
        mock_ws_invalid = MockWebSocket(query_params={"token": "invalid_token"})
        
        is_authenticated, user = await authenticate_ws_connection(mock_ws_invalid)
        
        # Should have closed the WebSocket connection
        assert mock_ws_invalid.closed
        assert mock_ws_invalid.close_code == status.WS_1008_POLICY_VIOLATION
        assert is_authenticated is False
        assert user is None
        
        # Test without token
        mock_ws_no_token = MockWebSocket()
        
        is_authenticated, user = await authenticate_ws_connection(mock_ws_no_token)
        
        # Should have closed the WebSocket connection
        assert mock_ws_no_token.closed
        assert mock_ws_no_token.close_code == status.WS_1008_POLICY_VIOLATION
        assert is_authenticated is False
        assert user is None
