import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.news.websocket_manager import connection_manager
from app.deps_ws import authenticate_ws_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/news", tags=["news"])


@router.websocket("/ws/{client_id}")
async def news_websocket(websocket: WebSocket, client_id: str):
    is_authenticated, user = await authenticate_ws_connection(websocket)

    if not is_authenticated:
        return

    await websocket.accept()
    await connection_manager.add(websocket, user)
    logger.info(f"Client {client_id} connected to news WebSocket")

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected from news WebSocket")
    except Exception as e:
        logger.error(f"Error in WebSocket connection for client {client_id}: {e}")
    finally:
        await connection_manager.remove(websocket)
