from typing import Optional, Callable, Any

import logging
import json
import websockets

from tenacity import (
    before_sleep_log,
    retry,
    stop_after_attempt,
    wait_exponential,
) 
from websockets.exceptions import WebSocketException

from app.core.config import settings
from app.core.news.types import NewsData
from app.utils import datetime_from_timestamp, pretty_print

# https://tenacity.readthedocs.io
# https://websockets.readthedocs.io/en/stable/

logger = logging.getLogger(__name__)

class TreeNews():
    """Fetch news from the TreeNews provider."""

    def __init__(self):
        self.wss = "wss://news.treeofalpha.com/ws"
        self._socket: Optional[websockets.WebSocketClientProtocol] = None
        self._callback: Optional[Callable[[NewsData], Any]] = None
        self._running = False

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def connect(self, callback: Callable[[NewsData], Any]):
        """Connect to the TreeNews WebSocket server with retry logic."""
        self._callback = callback
        self._running = True
        
        try:
            async with websockets.connect(self.wss) as websocket:
                self._socket = websocket
                await websocket.send(f"login {settings.TREENEWS_API_KEY}")
                logger.info("Connected to TreeNews WebSocket server and sent login")
                await self._listen()
        except WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
            raise
        finally:
            self._socket = None

    async def _listen(self):
        """Listen for incoming messages and process them."""
        if not self._socket:
            return

        while self._running:
            try:
                message = await self._socket.recv()
                await self._handle_message(message)
            except websockets.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                continue

    async def _handle_message(self, message: str):
        """
        Process incoming message and convert to NewsData object. 
        https://docs.treeofalpha.com/websockets/response
        """
        if not self._callback:
            return

        try:
            data = json.loads(message)
            
            if settings.ENVIRONMENT == "development": 
                pretty_print(data, ",\n")

            news = NewsData()
            news.source = data.get('source', '')
            news.icon = data.get('icon', '')
            news.feed = data.get('type', '')
            
            news.url = data.get('url', data.get('link', ''))
            news.title = data.get('title', data.get('en', ''))
            news.body = data.get('body', '')

            if news.source is None:
                news.source = "Twitter"
                
                info = data.get('info', {})
                news.is_quote = info.get('isQuote', False)
                news.is_reply = info.get('isReply', False)
                news.is_retweet = info.get('isRetweet', False)
                news.is_self_reply = info.get('isSelfReply', False)
            elif news.source == "Blogs":
                title_split = news.title.split(":")
                news.source = title_split[0].strip().lower().capitalize()
            else:
                news.source = "Other"
            
            news.image = data.get('image', '')
            news.time = datetime_from_timestamp(data.get('time', 0))

            coins = set()
            suggestions = data.get('suggestions', [])
            for suggestion in suggestions:
                if 'coin' in suggestion: coins.add(suggestion['coin'])
            news.coin = coins

            await self._callback(news)
        except Exception as e:
            logger.error(f"Error parsing message: {e}")

    async def disconnect(self):
        """Gracefully disconnect from the WebSocket server."""
        self._running = False

        if self._socket:
            await self._socket.close()
            self._socket = None
            logger.info("Disconnected from TreeNews WebSocket server")
