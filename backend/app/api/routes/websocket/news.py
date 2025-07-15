import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.news.news_manager import NewsManager
from app.deps_ws import authenticate_ws_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/news", tags=["news"])


@router.websocket("/ws/{client_id}")
async def news_websocket(websocket: WebSocket, client_id: str):
    is_authenticated, user = await authenticate_ws_connection(websocket)
    
    if not is_authenticated:
        return
    
    manager = NewsManager.get_instance() 

    try:
        await websocket.accept()
        await manager.add_client(websocket, user)
        logger.info(f"Client {client_id} connected to news WebSocket")
        
        # Keep the connection alive until client disconnects
        while True:
            data = await websocket.receive_json()
            
            if "type" not in data:
                continue

            if data["type"] == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected from news WebSocket")
    except Exception as e:
        logger.error(f"Error in WebSocket connection for client {client_id}: {e}")
    finally:
        await manager.remove_client(websocket) # clean up by clients from manager
        logger.info(f"Client {client_id} removed from news WebSocket manager")