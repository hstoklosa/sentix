import logging

from app.core.database import sessionmanager
from app.core.news.tree_news import TreeNews
from app.core.news.coindesk_news import CoinDeskNews
from app.core.news.types import NewsData
from app.core.news.websocket_manager import ConnectionManager
from app.services.llms import analyse_post_sentiment

logger = logging.getLogger(__name__)


class NewsIngestionService:
    """Connects to news providers, processes incoming news, and broadcasts to clients."""

    def __init__(self, connection_manager: ConnectionManager):
        self.providers = {
            "TreeNews": TreeNews(),
            "CoinDesk": CoinDeskNews(),
        }
        self.connection_manager = connection_manager
        self.is_initialized = False


    async def initialize(self):
        """Initialize connections to all news providers."""
        if self.is_initialized:
            return

        for name, provider in self.providers.items():
            await self._init_provider(provider, name)

        self.is_initialized = True
        logger.info("All news providers initialised")


    async def shutdown(self):
        """Shutdown and disconnect from all providers."""
        if not self.is_initialized:
            return

        for name, provider in self.providers.items():
            try:
                await provider.disconnect()
                logger.info(f"Disconnected from provider: {name}")
            except Exception as e:
                logger.error(f"Error disconnecting from provider {name}: {e}")

        self.is_initialized = False
        logger.info("Disconnected from all news providers")


    async def _init_provider(self, provider, name: str):
        """Initialise a single provider with proper error handling."""
        try:
            async def callback(news_data: NewsData):
                news_data.feed = name
                await self._on_news_received(news_data)

            await provider.connect(callback)
            logger.info(f"Successfully initialised provider: {name}")
        except Exception as e:
            logger.error(f"Failed to connect to provider {name}: {e}")


    async def _on_news_received(self, news_data: NewsData):
        """Process a news item and broadcast to connected clients."""
        saved_post = await self._process_and_save(news_data)
        if saved_post:
            from app.schemas.news import serialize_post_for_ws
            message = serialize_post_for_ws(saved_post)
            await self.connection_manager.broadcast(message)


    async def _process_and_save(self, news_data: NewsData):
        """Run sentiment analysis and persist the news item."""
        from app.services.news import save_news_item

        try:
            async with sessionmanager.session() as session:
                sentiment = await analyse_post_sentiment(news_data)
                saved_post = await save_news_item(session, news_data, sentiment)
                return saved_post
        except Exception as e:
            logger.error(f"Error processing news item: {e}")
            return None
