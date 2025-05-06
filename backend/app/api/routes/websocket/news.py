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
        
        while True:
            # Keep the connection alive until client disconnects
            data = await websocket.receive_json()
            logger.info(f"Received message from client {client_id}: {data}")
            
            if "type" not in data:
                continue
                
            message_type = data["type"]
            match message_type:
                case "ping":
                    await websocket.send_json({"type": "pong"})
                case "subscribe":
                    if "feed" in data and isinstance(data["feed"], str):
                        feed = data["feed"]
                        subscription = await manager.update_subscription(websocket, feed)
                        
                        if subscription:
                            await websocket.send_json({
                                "type": "subscribed", "feed": subscription
                            })
                        else:
                            await websocket.send_json({
                                "type": "error", "message": f"Feed '{feed}' not available"
                            })
                case "unsubscribe":
                    success = await manager.unsubscribe(websocket)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "success": success
                    })
                case "get_subscription":
                    subscription = await manager.get_subscription(websocket)
                    await websocket.send_json({
                        "type": "subscription",
                        "feed": subscription
                    })
                case "get_available_feeds":
                    feeds = await manager.get_available_feeds()
                    await websocket.send_json({
                        "type": "available_feeds",
                        "feeds": list(feeds)
                    })
                    logger.info(f"Sent available feeds to client {client_id}: {feeds}")
                case _:
                    logger.warning(f"Unknown message type from client {client_id}: {message_type}")
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected from news WebSocket")
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
    finally:
        await manager.remove_client(websocket) # clean up by clients from manager
        logger.info(f"Client {client_id} removed from news WebSocket manager")