import logging
from typing import Set, Dict, Any
from datetime import datetime

from fastapi import WebSocket
from app.core.news.tree_news import TreeNews
from app.core.news.types import NewsData

logger = logging.getLogger(__name__)

class NewsWebSocketManager:
    """
    A singleton manager that handles WebSocket connections between clients and TreeNews, acting as a middleman to broadcast TreeNews data to all connected clients. 
    """
    _instance = None
    
    def __init__(self):
        self.tree_news = TreeNews()
        self.active_clients: Set[WebSocket] = set()  # store WebSocket connections
        self.is_connected = False
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance of the manager"""
        if cls._instance is None:
            cls._instance = NewsWebSocketManager()

        return cls._instance
    
    async def connect_tree_news(self):
        """Connect to TreeNews if not already connected"""
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
    
    async def add_client(self, websocket: WebSocket):
        """
        Register a new client WebSocket connection
        
        Args:
            websocket: The WebSocket connection to add
        """
        self.active_clients.add(websocket)
        logger.info(f"Client added. Total clients: {len(self.active_clients)}")
        
        # Start TreeNews connection if this is the first client
        if len(self.active_clients) == 1:
            await self.connect_tree_news()
    
    async def remove_client(self, websocket: WebSocket):
        """
        Remove a client WebSocket connection
        
        Args:
            websocket: The WebSocket connection to remove
        """
        if websocket in self.active_clients:
            self.active_clients.remove(websocket)
            logger.info(f"Client removed. Total clients: {len(self.active_clients)}")
        
        # Disconnect from TreeNews if no clients left
        if len(self.active_clients) == 0 and self.is_connected:
            logger.info("No clients left, disconnecting from TreeNews")
            await self.tree_news.disconnect()
            self.is_connected = False
    
    async def broadcast_to_clients(self, news_data: NewsData):
        """
        Broadcast news data to all connected clients
        
        Args:
            news_data: The news data to broadcast
        """
        message = self.format_news_for_clients(news_data)
        
        disconnected_clients = set()
        
        for client in self.active_clients:
            try:
                await client.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected_clients.add(client)
        
        # Clean up disconnected clients
        for client in disconnected_clients:
            await self.remove_client(client)
    
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
                "link": news_data.link,
                "image": news_data.image,
                "icon": news_data.icon,
                "coins": list(news_data.coin) if news_data.coin else [],
                "feed": news_data.feed
            }
        } 