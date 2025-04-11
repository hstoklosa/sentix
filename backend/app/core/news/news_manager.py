from typing import Dict, Any, Optional
from datetime import datetime
import logging
import asyncio

from fastapi import WebSocket

from app.core.db import get_session
from app.models.user import User
from app.core.news.tree_news import TreeNews
from app.core.news.types import NewsData
from app.models.news import NewsItem
from app.services.news import save_news_item
from app.utils import format_datetime_iso

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """
    Class to store WebSocket connection information
    """
    def __init__(self, websocket: WebSocket, user: Optional[User] = None):
        self.websocket = websocket
        self.user = user
        self.connected_at = datetime.now()
        self.send_lock = asyncio.Lock()  # dedicated lock for sending messages

class NewsWebSocketManager:
    """
    A singleton manager that handles WebSocket connections between clients and TreeNews, 
    acting as a middleman to broadcast TreeNews data to all connected clients. 
    """
    _instance = None
    
    def __init__(self):
        self.tree_news = TreeNews()
        self.active_connections: Dict[WebSocket, WebSocketConnection] = {}
        self.connection_lock = asyncio.Lock()
        self.is_connected = False
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance of the manager"""
        if cls._instance is None:
            cls._instance = NewsWebSocketManager()

        return cls._instance
    
    async def connect_tree_news(self):
        """Connect to TreeNews if not already connected"""
        
        # Use lock to prevent multiple concurrent connection attempts
        async with self.connection_lock:
            if self.is_connected:
                return
                
            await self.tree_news.connect(self.on_news_received)
            self.is_connected = True
            logger.info("Connected to TreeNews service")
    
    async def on_news_received(self, news_data: NewsData):
        """
        Callback for when news is received from TreeNews
        
        Args:
            news_data: The news data received from TreeNews
        """
        logger.info(f"Received news: {news_data.title}")

        try:
            session = next(get_session())
            saved_post = await save_news_item(session, news_data)
            
            # TODO: Compute sentiment score, price forecast, filter, etc

            await self.broadcast_to_clients(saved_post)
        except Exception as e:
            logger.error(f"Error saving news to database: {str(e)}")
    
    async def add_client(self, websocket: WebSocket, user: Optional[User] = None):
        """
        Register a new client WebSocket connection
        
        Args:
            websocket: The WebSocket connection to add
            user: The authenticated user (optional)
        """
        self.active_connections[websocket] = WebSocketConnection(websocket, user)
        logger.info(f"Client added. Total clients: {len(self.active_connections)}")

        if len(self.active_connections) == 1:
            # Task to avoid blocking the client connection
            asyncio.create_task(self.connect_tree_news())

    async def remove_client(self, websocket: WebSocket):
        """
        Remove a client WebSocket connection
        
        Args:
            websocket: The WebSocket connection to remove
        """
        if websocket in self.active_connections:
            del self.active_connections[websocket]
            logger.info(f"Client removed. Total clients: {len(self.active_connections)}")
        
        # Disconnect from TreeNews if no clients left
        if len(self.active_connections) == 0 and self.is_connected:
            async with self.connection_lock:
                # Checking again as conditions might have changed
                if not self.is_connected:
                    return
                
                logger.info("No clients left, disconnecting from TreeNews")
                await self.tree_news.disconnect()
                self.is_connected = False
    
    async def send_to_client(self, websocket: WebSocket, connection: WebSocketConnection, message: Dict[str, Any]) -> bool:
        """
        Send a message to a specific client with proper locking
        
        Args:
            websocket: The WebSocket connection
            connection: The WebSocketConnection object
            message: The message to send
            
        Returns:
            True if the message was sent successfully, False otherwise
        """
        try:
            # Use the connection's dedicated send lock
            async with connection.send_lock:
                await websocket.send_json(message)
                
            return True
        except Exception as e:
            logger.error(f"Error sending to client: {e}")
            return False
    
    async def broadcast_to_clients(self, post: NewsItem):
        """
        Broadcast news data to all connected clients
        
        Args:
            news_data: The news data to broadcast
        """
        connections = list(self.active_connections.items())
        disconnected_websockets = []
        
        # Format the response structure including coins data 
        # and datetime serialization
        coins = []
        for news_coin in post.coins:
            coin = news_coin.coin
            coins.append({
                "id": coin.id,
                "symbol": coin.symbol,
                "name": coin.name
            })

        formatted_post = {
            "id": post.id,
            "_type": post.item_type,
            "title": post.title,
            "body": post.body,
            "source": post.source,
            "url": post.url,
            "icon_url": post.icon_url,
            "image_url": post.image_url,
            "feed": post.feed,
            "time": format_datetime_iso(post.time),
            "created_at": format_datetime_iso(post.created_at),
            "updated_at": format_datetime_iso(post.updated_at),
            "coins": coins
        }

        for websocket, connection in connections:
            success = await self.send_to_client(websocket, connection, {
                "type": "news",
                "data": formatted_post
            })

            if not success:
                disconnected_websockets.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected_websockets:
            await self.remove_client(websocket)
