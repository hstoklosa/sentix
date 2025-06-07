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
# from app.ml_models.sentiment_analysis import sentiment_analyser
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
        self.current_subscription: Optional[str] = None


class NewsManager:
    """
    A class responsible for managing WebSocket connections between clients and 
    news providers, acting as a middleman to broadcast news data.
    """
    _instance = None
    
    def __init__(self):
        self.providers: Dict[str, NewsProvider] = {
            "TreeNews": TreeNews(),
            "CoinDesk": CoinDeskNews()
        }
        self.active_connections: Dict[WebSocket, Connection] = {}
        self.is_initialized = False
        self.connection_lock = asyncio.Lock()
    
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
            if self.is_initialized:  # Double-check after acquiring lock
                return
            
            for provider_name, provider in self.providers.items():
                # Create a callback that captures provider_name in a closure
                # Each provider calls callback with just one argument (news_data)
                async def make_callback(pname=provider_name):
                    async def callback(news_data):
                        await self.on_news_received(news_data, pname)
                    return callback
                
                # Launch connection as a background task instead of waiting
                callback_fn = await make_callback()
                asyncio.create_task(self._connect_provider(provider, callback_fn, provider_name))
            
            self.is_initialized = True
    
    async def _connect_provider(self, provider: NewsProvider, callback_fn, provider_name: str):
        """Connect to a provider in the background with proper error handling"""
        try:
            logger.info(f"Connecting to provider: {provider_name}")
            await provider.connect(callback_fn)
            logger.info(f"Successfully connected to provider: {provider_name}")
        except Exception as e:
            logger.error(f"Failed to connect to provider {provider_name}: {str(e)}")
            # Don't re-raise the exception - we want to continue even if one provider fails
    
    async def shutdown(self):
        """Shutdown and disconnect from all providers"""
        if not self.is_initialized:
            return
            
        async with self.connection_lock:
            if not self.is_initialized:  # Double-check after acquiring lock
                return
                
            logger.info("Shutting down connections to all news providers")
            disconnect_tasks = []
            
            for provider in self.providers.values():
                disconnect_tasks.append(provider.disconnect())
            
            if disconnect_tasks:
                await asyncio.gather(*disconnect_tasks)
                
            self.is_initialized = False
            logger.info("Disconnected from all news providers")
    
    async def on_news_received(self, news_data: NewsData, provider_name: str):
        """
        Callback for when news is received from a provider
        
        Args:
            news_data: The news data received
            provider_name: The name of the provider that sent the news
        """
        try:
            async with sessionmanager.session() as session:
                news_data.feed = provider_name

                # TODO: Temporarily hardcode results of sentiment analysis
                # sentiment = sentiment_analyser.predict(news_data.body)
                # saved_post = await save_news_item(session, news_data, sentiment)

                saved_post = await save_news_item(session, news_data, {
                    "label": "neutral",
                    "score": 0.5,
                    "polarity": 0.0
                })

                await self.broadcast_to_clients(saved_post)
        except Exception as e:
            logger.error(f"Error processing news item: {str(e)}")
    
    async def add_client(self, websocket: WebSocket, user: Optional[User] = None):
        """
        Register a new client WebSocket connection
        
        Args:
            websocket: The WebSocket connection to add
            user: The authenticated user (optional)
        """
        try:
            if not self.is_initialized:
                logger.info("First client connecting, initializing providers")
                await self.initialize()
                
            connection = Connection(websocket, user)
            self.active_connections[websocket] = connection
        except Exception as e:
            logger.error(f"Error adding client: {str(e)}")
            # Don't re-raise to avoid crashing the websocket handler

    async def remove_client(self, websocket: WebSocket):
        """
        Remove a client WebSocket connection
        
        Args:
            websocket: The WebSocket connection to remove
        """
        if websocket in self.active_connections:
            del self.active_connections[websocket]
    
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
            connection.current_subscription = provider_name
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
        try:
            # Make a safe copy of connections to avoid mutation during iteration
            connections = list(self.active_connections.items())
            disconnected_websockets = []

            message = {
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
            }

            subscribed_count = 0
            for websocket, connection in connections:

                if connection.current_subscription == post.feed:
                    subscribed_count += 1
                    username = connection.user.username if connection.user else "Anonymous"
                    logger.info(f"Sending news to subscribed client {username} (feed: {post.feed})")
                    
                    try:
                        success = await self.send_to_client(websocket, connection, message)
                        if not success:
                            logger.warning(f"Failed to send news to client, marking for disconnection")
                            disconnected_websockets.append(websocket)
                    except Exception as e:
                        disconnected_websockets.append(websocket)
            
            for websocket in disconnected_websockets:
                await self.remove_client(websocket)
                
        except Exception as e:
            logger.error(f"Error in broadcast_to_clients: {str(e)}")
