import logging
import asyncio
from typing import Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Depends
from app.core.news.news_manager import NewsManager
from app.deps_ws import authenticate_ws_connection
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/news", tags=["news"])

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
        return
    
    # Log successful authentication
    user_info = f"User {user.username} (ID: {user.id})" if user else "Anonymous"
    logger.info(f"Authenticated WebSocket connection from {user_info}, client ID: {client_id}")
    
    manager = NewsManager.get_instance() 
    
    try:
        await websocket.accept()
        await manager.add_client(websocket, user)
        
        logger.info(f"Client {client_id} connected to news WebSocket")
        
        # Keep the connection alive until client disconnects
        while True:
            try:
                # Wait for messages from the client
                data = await websocket.receive_json()
                logger.info(f"Received message from client {client_id}: {data}")
                
                if "type" not in data:
                    continue
                    
                message_type = data["type"]
                
                if message_type == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message_type == "subscribe":
                    if "feed" in data and isinstance(data["feed"], str):
                        feed = data["feed"]
                        subscription = await manager.update_subscription(websocket, feed)
                        
                        if subscription:
                            await websocket.send_json({
                                "type": "subscribed",
                                "feed": subscription
                            })
                        else:
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Feed '{feed}' not available"
                            })
                elif message_type == "unsubscribe":
                    success = await manager.unsubscribe(websocket)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "success": success
                    })
                elif message_type == "get_subscription":
                    subscription = await manager.get_subscription(websocket)
                    await websocket.send_json({
                        "type": "subscription",
                        "feed": subscription
                    })
                elif message_type == "get_available_feeds":
                    feeds = await manager.get_available_feeds()
                    await websocket.send_json({
                        "type": "available_feeds",
                        "feeds": list(feeds)
                    })
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected from news WebSocket")
                break
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
    finally:
        # Clean up by removing the client from the manager
        await manager.remove_client(websocket)
        logger.info(f"Client {client_id} removed from news WebSocket manager")