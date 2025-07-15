from typing import List, Dict, Any, Optional
import logging

from app.core.config import settings
from app.core.market.base_client import BaseApiClient

logger = logging.getLogger(__name__)


class CoinGeckoClient(BaseApiClient):
    _API_BASE_URL = "https://api.coingecko.com/api/v3"
    _API_KEY = settings.COINGECKO_API_KEY
    
    _COINS_MARKETS_TTL = 300  # 5 minutes
    _COIN_MARKET_CHART_TTL = 900  # 15 minutes

    def __init__(self):
        headers = { "x-cg-demo-api-key": self._API_KEY }
        super().__init__(self._API_BASE_URL, headers)
        
        self.set_cache_ttl("/coins/markets", self._COINS_MARKETS_TTL)
        self.set_cache_ttl("/coins/{id}/market_chart", self._COIN_MARKET_CHART_TTL)
    
    def _parse_next_update_time(self, response_data: Dict[str, Any]) -> Optional[int]:
        """Extract next update time from CoinGecko response if available"""
        # CoinGecko doesn't provide information about next update time
        return None

    async def get_coins_markets(self,
        vs: str = "usd",
        page: int = 1,
        limit: int = 250,
        symbols: Optional[List[str]] = None, 
        include_tokens: str = "top",
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """Get list of coins with market data"""
        params = {
            "vs_currency": vs,
            "page": page,
            "per_page": limit,
            "order": "market_cap_desc",
            "sparkline": "false",
        }
        
        if symbols:
            params["symbols"] = ",".join(symbols)
            params["include_tokens"] = include_tokens
            
        return await self._send_request(
            "/coins/markets", params=params, force_refresh=force_refresh
        ) or []
        
    async def get_coin_market_chart(self,
        coin_id: str,
        vs: str = "usd",
        days: int = 30,
        interval: str = "daily",
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Get historical market data for a specific coin"""
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