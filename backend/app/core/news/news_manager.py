from typing import Dict, Any, Optional, Set, Callable
from datetime import datetime

import logging
import asyncio
from fastapi import WebSocket

from app.core.db import get_session
from app.core.news.tree_news import TreeNews
from app.core.news.types import NewsData, NewsProvider
from app.models.user import User
from app.models.news import NewsItem
from app.ml_models import cryptobert
from app.services.news import save_news_item
from app.utils import format_datetime_iso

logger = logging.getLogger(__name__)


class Connection:
    """Class to store information about a WebSocket connection"""
    def __init__(self, websocket: WebSocket, user: Optional[User] = None):
        self.websocket = websocket
        self.user = user
        self.connected_at = datetime.now()
        self.send_lock = asyncio.Lock()
        self.current_subscription: Optional[str] = None  # Single provider subscription


class NewsManager:
    """
    A singleton manager that handles WebSocket connections between clients and news providers, 
    acting as a middleman to broadcast news data to subscribed clients. 
    """
    _instance = None
    
    def __init__(self):
        # Dictionary of provider name to provider instance
        self.providers: Dict[str, NewsProvider] = {
            "TreeNews": TreeNews()
            # Add other providers here as they become available
        }
        
        # Track which providers are connected
        self.connected_providers: Set[str] = set()
        
        self.active_connections: Dict[WebSocket, Connection] = {}
        self.connection_lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance of the manager"""
        if cls._instance is None:
            cls._instance = NewsManager()

        return cls._instance
    
    async def connect_provider(self, provider_name: str):
        """
        Connect to a specific news provider if not already connected.
        
        Args:
            provider_name: The name of the provider to connect to
        """
        if provider_name not in self.providers:
            logger.warning(f"Unknown provider: {provider_name}")
            return
            
        async with self.connection_lock:
            if provider_name in self.connected_providers:
                return
                
            provider = self.providers[provider_name]
            await provider.connect(lambda news_data: self.on_news_received(news_data, provider_name))
            self.connected_providers.add(provider_name)
            logger.info(f"Connected to {provider_name}")
    
    async def on_news_received(self, news_data: NewsData, provider_name: str):
        """
        Callback for when news is received from a provider
        
        Args:
            news_data: The news data received
            provider_name: The name of the provider that sent the news
        """
        try:
            session = next(get_session())
            
            # Set the feed name to the provider name
            news_data.feed = provider_name
            
            sentiment = cryptobert.predict_sentiment(news_data.body)
            saved_post = await save_news_item(session, news_data, sentiment)
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
        connection = Connection(websocket, user)
        
        # By default, subscribe to the first available provider
        if self.providers:
            connection.current_subscription = next(iter(self.providers.keys()))
        
        self.active_connections[websocket] = connection

        # Connect to provider if this is the first client
        if len(self.active_connections) == 1 and connection.current_subscription:
            asyncio.create_task(self.connect_provider(connection.current_subscription))

    async def remove_client(self, websocket: WebSocket):
        """
        Remove a client WebSocket connection and disconnect from providers if no clients are left
        
        Args:
            websocket: The WebSocket connection to remove
        """
        if websocket in self.active_connections:
            del self.active_connections[websocket]
        
        # If no more connections, disconnect from all providers
        if not self.active_connections:
            async with self.connection_lock:
                for provider_name in list(self.connected_providers):
                    if provider_name in self.providers:
                        provider = self.providers[provider_name]
                        await provider.disconnect()
                self.connected_providers.clear()
                logger.info("Disconnected from all providers")
    
    async def update_subscription(self, websocket: WebSocket, provider_name: str) -> Optional[str]:
        """
        Update a client's subscription to a single provider
        
        Args:
            websocket: The WebSocket connection
            provider_name: Name of the feed to subscribe to
            
        Returns:
            The name of the provider subscribed to, or None if invalid
        """
        connection = self.active_connections.get(websocket)
        if not connection:
            return None
            
        # Only update if the provider exists
        if provider_name in self.providers:
            old_subscription = connection.current_subscription
            connection.current_subscription = provider_name
            
            # Connect to the newly subscribed provider if not already connected
            if provider_name not in self.connected_providers:
                asyncio.create_task(self.connect_provider(provider_name))
            
            return provider_name
        
        return connection.current_subscription
    
    async def unsubscribe(self, websocket: WebSocket) -> bool:
        """
        Remove client's current subscription
        
        Args:
            websocket: The WebSocket connection
            
        Returns:
            True if unsubscribed successfully, False otherwise
        """
        connection = self.active_connections.get(websocket)
        if not connection:
            return False
            
        connection.current_subscription = None
        return True
    
    async def get_subscription(self, websocket: WebSocket) -> Optional[str]:
        """
        Get a client's current subscription
        
        Args:
            websocket: The WebSocket connection
            
        Returns:
            The current provider subscription or None
        """
        connection = self.active_connections.get(websocket)
        return connection.current_subscription if connection else None
    
    async def get_available_feeds(self) -> Set[str]:
        """
        Get the names of all available news feeds
        
        Returns:
            Set of available feed names
        """
        return set(self.providers.keys())
    
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
        Broadcast news data to subscribed clients
        
        Args:
            post: The news post to broadcast
        """
        connections = list(self.active_connections.items())
        disconnected_websockets = []
        
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
            "coins": post.get_formatted_coins(),
            "sentiment": post.sentiment,
            "score": post.score
        }

        for websocket, connection in connections:
            # Only send to clients subscribed to this feed
            if connection.current_subscription == post.feed:
                success = await self.send_to_client(websocket, connection, {
                    "type": "news",
                    "data": formatted_post
                })

                if not success:
                    disconnected_websockets.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected_websockets:
            await self.remove_client(websocket)
