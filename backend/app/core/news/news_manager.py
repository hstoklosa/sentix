from typing import Dict, Any, Optional, Set
from datetime import datetime
import logging
import asyncio

from fastapi import WebSocket

from app.core.database import sessionmanager
from app.core.news.tree_news import TreeNews
from app.core.news.coindesk_news import CoinDeskNews
from app.core.news.types import NewsData, NewsProvider
from app.models.user import User
from app.models.news import NewsItem
from app.ml_models.sentiment_analysis import sentiment_analyser
# Removed to avoid circular import - will import inside function
from app.utils import format_datetime_iso

logger = logging.getLogger(__name__)


class Connection:
    """Class to store information about a WebSocket connection"""
    def __init__(self, websocket: WebSocket, user: Optional[User] = None):
        self.websocket = websocket
        self.user = user
        self.send_lock = asyncio.Lock()


class NewsManager:
    """Class responsible for managing connections between clients and news providers."""
    _instance = None
    
    def __init__(self):
        self.providers: Dict[str, NewsProvider] = {
            "TreeNews": TreeNews(),
            "CoinDesk": CoinDeskNews()
        }
        self.is_initialized = False
        self.connection_lock = asyncio.Lock()
        self.active_connections: Dict[WebSocket, Connection] = {}
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance of the manager"""
        if cls._instance is None:
            cls._instance = NewsManager()
        return cls._instance
    
    async def initialize(self):
        """Initialize connections to all news providers"""
        if self.is_initialized:
            return
            
        async with self.connection_lock:
            if self.is_initialized:
                return

            # Create a single callback handler for all providers
            init_tasks = []
            for provider_name, provider in self.providers.items():
                init_tasks.append(self._init_provider(provider, provider_name))

            await asyncio.gather(*init_tasks)
            self.is_initialized = True
            logger.info("All news providers initialised")
    
    async def _init_provider(self, provider: NewsProvider, provider_name: str):
        """Initialise a single provider with proper error handling"""
        try:
            async def callback(news_data: NewsData):
                news_data.feed = provider_name
                await self.on_news_received(news_data, provider_name)
            
            # Connect to the provider directly (no background task)
            await provider.connect(callback)
            logger.info(f"Successfully initialised provider: {provider_name}")
        except Exception as e:
            logger.error(f"Failed to connect to provider {provider_name}: {str(e)}")
    
    async def shutdown(self):
        """Shutdown and disconnect from all providers"""
        if not self.is_initialized:
            return
            
        async with self.connection_lock:
            if not self.is_initialized:
                return

            disconnect_tasks = []
            
            for provider_name, provider in self.providers.items():
                disconnect_tasks.append(self._disconnect_provider(provider, provider_name))
            
            await asyncio.gather(*disconnect_tasks)
            self.is_initialized = False
            logger.info("Disconnected from all news providers")
    
    async def _disconnect_provider(self, provider: NewsProvider, provider_name: str):
        """Disconnect a provider with error handling"""
        try:
            await provider.disconnect()
            logger.info(f"Disconnected from provider: {provider_name}")
        except Exception as e:
            logger.error(f"Error disconnecting from provider {provider_name}: {str(e)}")

    async def on_news_received(self, news_data: NewsData, provider_name: str):
        """
        Callback for when news is received from a provider
        
        Args:
            news_data: The news data received
            provider_name: The name of the provider that sent the news
        """
        if saved_post := await self._process_news_item(news_data, provider_name):
            await self.broadcast_to_clients(saved_post)

    async def _process_news_item(self, news_data: NewsData, provider_name: str):
        """Process a news item from a provider"""
        from app.services.news import save_news_item  # Import here to avoid circular import
        
        try:
            async with sessionmanager.session() as session:
                news_data.feed = provider_name
                sentiment = sentiment_analyser.predict(news_data.body)
                saved_post = await save_news_item(session, news_data, sentiment)
                return saved_post
        except Exception as e:
            logger.error(f"Error processing news item: {str(e)}")
            return None
    
    async def send_to_client(self, websocket: WebSocket, connection: Connection, message: Dict[str, Any]) -> bool:
        """
        Send a message to a specific client with proper locking
        
        Args:
            websocket: The WebSocket connection
            connection: The Connection object
            message: The message to send
            
        Returns:
            True if the message was sent successfully, False otherwise
        """
        try:
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
            post: The news post to broadcast
        """
        try:
            # Make a safe copy of connections to avoid mutation during iteration
            connections = list(self.active_connections.items())
            disconnected_websockets = []

            for websocket, connection in connections:
                try:
                    success = await self.send_to_client(websocket, connection, {
                        "type": "news",
                        "data": {
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
                            "coins": post.get_formatted_coins(),
                            "sentiment": post.sentiment,
                            "score": post.score
                        }
                    })

                    if not success:
                        logger.warning(f"Failed to send news to client, marking for disconnection")
                        disconnected_websockets.append(websocket)

                except Exception as e:
                    logger.error(f"Exception while sending to client: {str(e)}")
                    disconnected_websockets.append(websocket)
            
            for websocket in disconnected_websockets:
                await self.remove_client(websocket)
                
        except Exception as e:
            logger.error(f"Error in broadcast_to_clients: {str(e)}")

    async def add_client(self, websocket: WebSocket, user: Optional[User] = None):
        """
        Register a new client WebSocket connection
        
        Args:
            websocket: The WebSocket connection to add
            user: The authenticated user (optional)
        """
        try:
            connection = Connection(websocket, user)
            self.active_connections[websocket] = connection
            logger.info(f"Added client. Total active connections: {len(self.active_connections)}")
        except Exception as e:
            logger.error(f"Error adding client: {str(e)}")

    async def remove_client(self, websocket: WebSocket):
        """
        Remove a client WebSocket connection
        
        Args:
            websocket: The WebSocket connection to remove
        """
        if websocket in self.active_connections:
            del self.active_connections[websocket]
            logger.info(f"Removed client. Total active connections: {len(self.active_connections)}")
        else:
            logger.warning(f"Attempted to remove client that was not in active connections")
    