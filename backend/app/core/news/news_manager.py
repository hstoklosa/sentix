import logging
from typing import Set, Dict, Any, Optional
from datetime import datetime
import asyncio

from fastapi import WebSocket
from app.core.news.tree_news import TreeNews
from app.core.news.types import NewsData
from app.models.user import User

logger = logging.getLogger(__name__)

class WebSocketConnection:
    """
    Class to store WebSocket connection information
    """
    def __init__(self, websocket: WebSocket, user: Optional[User] = None):
        self.websocket = websocket
        self.user = user
        self.connected_at = datetime.now()
        self.send_lock = asyncio.Lock()  # Add a dedicated lock for sending messages

class NewsWebSocketManager:
    """
    A singleton manager that handles WebSocket connections between clients and TreeNews, acting as a middleman to broadcast TreeNews data to all connected clients. 
    """
    _instance = None
    
    def __init__(self):
        self.tree_news = TreeNews()
        self.active_connections: Dict[WebSocket, WebSocketConnection] = {}  # store WebSocket connections with user info
        self.is_connected = False
        self.connection_lock = asyncio.Lock()  # Add a lock for TreeNews connection management
    
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
            if not self.is_connected:
                logger.info("Connecting to TreeNews service...")
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

        # TODO: Save to db, compute sentiment, etc...
        
        await self.broadcast_to_clients(news_data)
    
    async def add_client(self, websocket: WebSocket, user: Optional[User] = None):
        """
        Register a new client WebSocket connection
        
        Args:
            websocket: The WebSocket connection to add
            user: The authenticated user (optional)
        """
        self.active_connections[websocket] = WebSocketConnection(websocket, user)
        logger.info(f"Client added. Total clients: {len(self.active_connections)}")
        
        # Start TreeNews connection if this is the first client
        if len(self.active_connections) == 1:
            # Use a task to avoid blocking the client connection
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
                if self.is_connected:
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
    
    async def broadcast_to_clients(self, news_data: NewsData):
        """
        Broadcast news data to all connected clients
        
        Args:
            news_data: The news data to broadcast
        """
        message = self.format_news_for_clients(news_data)
        disconnected_websockets = []
        
        # Create a copy of the connections to avoid modification during iteration
        connections = list(self.active_connections.items())
        
        # Send the message to each client
        for websocket, connection in connections:
            success = await self.send_to_client(websocket, connection, message)
            if not success:
                disconnected_websockets.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected_websockets:
            await self.remove_client(websocket)
    
    def format_news_for_clients(self, news_data: NewsData) -> Dict[str, Any]:
        """
        Convert NewsData to a client-friendly format
        
        Args:
            news_data: The news data to format
            
        Returns:
            A dictionary with the formatted news data
        """
        return {
            "type": "news",
            "data": {
                "title": news_data.title,
                "body": news_data.body,
                "source": news_data.source,
                "time": news_data.time.isoformat() if isinstance(news_data.time, datetime) else news_data.time,
                "url": news_data.url,
                "image": news_data.image,
                "icon": news_data.icon,
                "coins": list(news_data.coin) if news_data.coin else [],
                "feed": news_data.feed
            }
        } 