import logging
import asyncio
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Depends
from app.core.news.news_manager import NewsWebSocketManager
from app.deps_ws import authenticate_ws_connection
from app.models.user import User
from app.deps import CurrentUserDep
from app.schemas.websocket import WebSocketConnectionInfo

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/news", tags=["news"])

@router.get("/ws-info", response_model=WebSocketConnectionInfo)
async def get_websocket_info(current_user: CurrentUserDep) -> WebSocketConnectionInfo:
    """
    Get information needed to connect to the WebSocket endpoint.
    This endpoint requires authentication and returns the WebSocket URL
    with the access token as a query parameter.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        WebSocketConnectionInfo: Information needed to connect to the WebSocket
    """
    from app.core.security import create_access_token
    
    # Create a fresh access token for the WebSocket connection
    access_token = create_access_token(data={"sub": str(current_user.id)})
    
    return WebSocketConnectionInfo(
        websocket_url=f"/api/v1/news/ws/{current_user.id}?token={access_token}"
    )

@router.websocket("/ws/{client_id}")
async def news_websocket(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for receiving real-time news updates
    
    Args:
        websocket: The WebSocket connection
        client_id: A unique identifier for the client
    """
    # Authenticate the WebSocket connection
    is_authenticated, user = await authenticate_ws_connection(websocket)
    
    if not is_authenticated:
        logger.warning(f"Unauthorized WebSocket connection attempt from client {client_id}")
        return  # Connection already closed by authenticate_ws_connection
    
    # Log successful authentication
    user_info = f"User {user.username} (ID: {user.id})" if user else "Anonymous"
    logger.info(f"Authenticated WebSocket connection from {user_info}, client ID: {client_id}")
    
    # Singleton manager instance
    manager = NewsWebSocketManager.get_instance() 
    
    # Accept the connection and add to manager
    await websocket.accept()
    await manager.add_client(websocket, user)
    
    logger.info(f"Client {client_id} connected to news WebSocket")
    
    # Create a receive lock for this specific connection
    receive_lock = asyncio.Lock()
    
    try:
        while True:
            # Use the lock to ensure only one receive operation at a time
            async with receive_lock:
                try:
                    # Wait for messages from the client
                    data = await websocket.receive_json()
                    logger.info(f"Received message from client {client_id}: {data}")
                    
                    # Handle ping messages
                    if "type" in data and data["type"] == "ping":
                        await websocket.send_json({"type": "pong"})
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Don't re-raise the exception, just continue the loop
                    # This prevents the WebSocket from disconnecting on errors
                    await asyncio.sleep(0.1)  # Small delay to prevent tight loop
                    continue
            
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected from news WebSocket")
    except Exception as e:
        logger.error(f"Error in news WebSocket connection with client {client_id}: {e}")
    finally:
        # Clean up by removing the client from the manager
        await manager.remove_client(websocket)