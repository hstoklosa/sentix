# https://tenacity.readthedocs.io
# https://websockets.readthedocs.io/en/stable/

from typing import Optional, Callable, Any
from datetime import datetime, timezone

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

from app.core.news.types import NewsData

logger = logging.getLogger(__name__)
api_key = "treenews_api_key"


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
                await websocket.send(f"login {api_key}")
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
        """Process incoming message and convert to NewsData object. 
        https://docs.treeofalpha.com/websockets/response
        """
        if not self._callback:
            return

        try:
            data = json.loads(message)
            news = NewsData()
            
            news.title = data.get('title', '')
            news.link = data.get('link', '')
            news.body = data.get('body', '')
            news.image = data.get('image', '')
            
            info = data.get('info', {})
            news.is_quote = info.get('isQuote', False)
            news.is_reply = info.get('isReply', False)
            news.is_retweet = info.get('isRetweet', False)
            
            # not provided in TreeNews response format
            news.quote_message = ''
            news.quote_user = ''
            news.quote_image = ''
            news.reply_user = ''
            news.reply_message = ''
            news.reply_image = ''
            news.retweet_user = ''
            
            news.icon = data.get('icon', '')
            news.source = data.get('source', '')
            news.time = datetime.fromtimestamp(data.get('time', 0) / 1000, tz=timezone.utc)  # convert from milliseconds
            
            # handle coin data from suggestions
            coins = set()
            suggestions = data.get('suggestions', [])
            for suggestion in suggestions:
                if 'coin' in suggestion:
                    coins.add(suggestion['coin'])
            news.coin = coins
            
            news.feed = data.get('type', '')  # 'direct' or other types
            news.sfx = '' # no sound effects
            news.ignored = not data.get('requireInteraction', True)

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
