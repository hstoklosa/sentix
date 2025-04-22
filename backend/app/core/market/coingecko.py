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
    _COIN_MARKET_CHART_TTL = 900  # 15 minutes

    def __init__(self):
        headers = { "x-cg-demo-api-key": self._API_KEY }
        super().__init__(self._API_BASE_URL, headers)
        
        # Set cache TTLs for specific endpoints
        self.set_cache_ttl("/coins/markets", self._COINS_MARKETS_TTL)
        self.set_cache_ttl("/coins/{id}/market_chart", self._COIN_MARKET_CHART_TTL)
    
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
        
    async def get_coin_market_chart(self,
        coin_id: str,
        vs: str = "usd",
        days: int = 30,
        interval: str = "daily",
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Get historical market data for a specific coin
        
        Args:
            coin_id: The coin id (e.g., bitcoin)
            vs: The target currency (e.g., usd)
            days: Data up to number of days ago (1, 7, 14, 30, 90, 180, 365, max)
            interval: Data interval (daily, hourly)
            force_refresh: Force refresh the cache
            
        Returns:
            Dict with prices, market_caps, and total_volumes arrays
        """
        return await self._send_request(
            f"/coins/{coin_id}/market_chart", 
            params = {
                "vs_currency": vs,
                "days": days,
                "interval": interval,
            }, 
            force_refresh=force_refresh
        ) or {"prices": [], "market_caps": [], "total_volumes": []}


coingecko_client = CoinGeckoClient()