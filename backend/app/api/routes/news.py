import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.news.news_manager import NewsWebSocketManager

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
    # Singleton manager instance
    manager = NewsWebSocketManager.get_instance() 
    
    await websocket.accept()
    await manager.add_client(websocket)
    
    logger.info(f"Client {client_id} connected to news WebSocket")
    
    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_json()
            logger.info(f"Received message from client {client_id}: {data}")
            
            if "type" in data and data["type"] == "ping":
                await websocket.send_json({"type": "pong"})
            
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected from news WebSocket")
    except Exception as e:
        logger.error(f"Error in news WebSocket connection with client {client_id}: {e}")
    finally:
        await manager.remove_client(websocket)  # ensure client is removed on disconnect