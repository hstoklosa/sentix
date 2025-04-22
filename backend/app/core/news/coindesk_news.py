from typing import Optional, Callable, Any, Dict, List
import logging
import asyncio
import aiohttp
from datetime import datetime

from tenacity import (
    before_sleep_log,
    retry,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.news.types import NewsData
from app.utils import datetime_from_timestamp

logger = logging.getLogger(__name__)

class CoinDeskNews:
    """Fetch news from the CoinDesk API."""
    
    def __init__(self):
        self.api_url = "https://data-api.coindesk.com/news/v1/article/list"
        self._callback: Optional[Callable[[NewsData], Any]] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_article_id: Optional[int] = None
        self._headers = {
            "X-API-KEY": settings.COINDESK_API_KEY,
            "Accept": "application/json"
        }
    
    async def connect(self, callback: Callable[[NewsData], Any]):
        """
        Start polling the CoinDesk API for news.
        
        Args:
            callback: Function to call when news is received
        """
        if self._running:
            return
            
        self._callback = callback
        self._running = True
        
        # Create and start the polling task
        self._task = asyncio.create_task(self._poll_articles())
        logger.info("Started CoinDesk news polling")
    
    async def disconnect(self):
        """Stop polling the CoinDesk API."""
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        logger.info("Stopped CoinDesk news polling")
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _fetch_articles(self) -> List[Dict[str, Any]]:
        """
        Fetch articles from the CoinDesk API.
        
        Returns:
            List of article dictionaries
        """
        params = {
            "lang": "EN",
            "limit": 20  # Adjust as needed
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_url, params=params, headers=self._headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error fetching CoinDesk news: {response.status} - {error_text}")
                    return []
                
                data = await response.json()
                
                if "Data" not in data:
                    logger.error(f"Invalid response format from CoinDesk API: {data}")
                    return []
                
                return data["Data"]
    
    async def _poll_articles(self):
        """Continuously poll the CoinDesk API for new articles."""
        while self._running:
            try:
                articles = await self._fetch_articles()
                
                # Process articles in reverse order (oldest first)
                # This ensures we maintain chronological order for the news feed
                for article in reversed(articles):
                    # Skip articles we've already processed
                    if self._last_article_id is not None and article["ID"] <= self._last_article_id:
                        continue
                    
                    # Update the last article ID
                    if self._last_article_id is None or article["ID"] > self._last_article_id:
                        self._last_article_id = article["ID"]
                    
                    # Convert to NewsData and send to callback
                    await self._process_article(article)
                
                # Wait for the configured interval before polling again
                await asyncio.sleep(settings.COINDESK_API_POLL_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error polling CoinDesk API: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying after an error
    
    async def _process_article(self, article: Dict[str, Any]):
        """
        Process an article from the CoinDesk API and convert it to NewsData.
        
        Args:
            article: Article data from the API
        """
        if not self._callback:
            return
        
        try:
            news = NewsData()
            news.feed = "CoinDesk"
            news.source = article.get("SOURCE_DATA", {}).get("NAME", "CoinDesk")
            news.icon = article.get("SOURCE_DATA", {}).get("IMAGE_URL", "")
            news.url = article.get("URL", "")
            news.title = article.get("TITLE", "")
            news.body = article.get("BODY", "")
            news.image = article.get("IMAGE_URL", "")
            
            # Convert timestamp to datetime
            # CoinDesk API provides Unix timestamp in seconds, but our utility expects milliseconds
            published_ts = article.get("PUBLISHED_ON", 0)
            # Convert seconds to milliseconds by multiplying by 1000
            news.time = datetime_from_timestamp(published_ts * 1000)
            
            # Log the timestamp conversion for debugging
            if settings.ENVIRONMENT == "development":
                logger.debug(f"Raw timestamp: {published_ts}, Converted time: {news.time}")
            
            # Extract coin information from categories
            news.coins = set()
            for category in article.get("CATEGORY_DATA", []):
                # Extract potential cryptocurrency symbols from category names
                category_name = category.get("NAME", "").strip()
                if category_name.isupper() and len(category_name) <= 5:
                    # Simple heuristic for detecting crypto symbols (e.g., BTC, ETH)
                    news.coins.add(category_name)
            
            # Default values for Twitter-specific fields
            news.is_reply = False
            news.is_self_reply = False
            news.is_quote = False
            news.is_retweet = False
            
            await self._callback(news)
            
        except Exception as e:
            logger.error(f"Error processing CoinDesk article: {e}") 