import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.market.base_client import BaseApiClient

logger = logging.getLogger(__name__)


class CoinMarketCapClient(BaseApiClient):
    _API_BASE_URL = "https://pro-api.coinmarketcap.com"
    _API_KEY = settings.COINMARKETCAP_API_KEY
    
    _MARKET_STATS_TTL = 300  # 5 minutes
    _FEAR_GREED_TTL = 900  # 15 minutes

    def __init__(self):
        headers = { "X-CMC_PRO_API_KEY": self._API_KEY }
        super().__init__(self._API_BASE_URL, headers)
        
        self.set_cache_ttl("/v1/global-metrics/quotes/latest", self._MARKET_STATS_TTL)
        self.set_cache_ttl("/v3/fear-and-greed/latest", self._FEAR_GREED_TTL)
    
    def _parse_next_update_time(self, response_data: Dict[str, Any]) -> Optional[int]:
        """Extract next update time from CoinMarketCap response if available"""
        try:
            # CoinMarketCap provides status.timestamp for when the data was generated
            # However, they don't explicitly provide next update time
            # We can approximate based on the timestamp and known update frequency
            status = response_data.get("status", {})
            if "timestamp" in status:
                timestamp_str = status["timestamp"]
                # Format is like: "2023-04-26T23:12:29.000Z"
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                
                # If URL contains fear-and-greed, use fear/greed TTL
                if "fear-and-greed" in status.get("credit_count", ""):
                    next_update = timestamp + timedelta(seconds=self._FEAR_GREED_TTL)
                else:
                    next_update = timestamp + timedelta(seconds=self._MARKET_STATS_TTL)
                
                # Calculate seconds until next update
                now = datetime.now()
                delta = next_update - now
                
                return max(60, int(delta.total_seconds()))  # At least 60 seconds
        except Exception as e:
            logger.warning(f"Error parsing next update time: {str(e)}")
        
        return None

    async def get_market_stats(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get a summary of the cryptocurrency market statistics."""
        return await self._send_request("/v1/global-metrics/quotes/latest", force_refresh=force_refresh)

    async def get_fear_greed_index(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get the Fear and Greed Index."""
        return await self._send_request("/v3/fear-and-greed/latest", force_refresh=force_refresh)


cmc_client = CoinMarketCapClient()