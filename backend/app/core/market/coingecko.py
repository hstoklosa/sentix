from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.market.base_client import BaseApiClient

logger = logging.getLogger(__name__)


class CoinGeckoClient(BaseApiClient):
    _API_BASE_URL = "https://api.coingecko.com/api/v3"
    _API_KEY = settings.COINGECKO_API_KEY
    
    # TTL constants for different endpoints (in seconds)
    _COINS_MARKETS_TTL = 300  # 5 minutes

    def __init__(self):
        headers = { "x-cg-demo-api-key": self._API_KEY }
        super().__init__(self._API_BASE_URL, headers)
        
        # Set cache TTLs for specific endpoints
        self.set_cache_ttl("/coins/markets", self._COINS_MARKETS_TTL)
    
    def _parse_next_update_time(self, response_data: Dict[str, Any]) -> Optional[int]:
        """
        Extract next update time from CoinGecko response if available
        
        Returns:
            Seconds until next update or None if not available
        """
        # CoinGecko doesn't provide explicit information about next update time
        # We could check response headers for rate limiting info, but that's not 
        # directly related to data freshness
        return None

    async def get_coins_markets(self,
        vs: str = "usd",
        page: int = 1,
        limit: int = 250,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """Get list of coins with market data"""
        return await self._send_request("/coins/markets", params = {
            "vs_currency": vs,
            "page": page,
            "per_page": limit,
            "order": "market_cap_desc",
            "sparkline": "false",
        }, force_refresh=force_refresh) or []


coingecko_client = CoinGeckoClient()