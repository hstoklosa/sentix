from typing import List, Dict, Any
import logging

from app.core.config import settings
from app.core.market.base_client import BaseApiClient

logger = logging.getLogger(__name__)


class CoinGeckoClient(BaseApiClient):
    _API_BASE_URL = "https://api.coingecko.com/api/v3"
    _API_KEY = settings.COINGECKO_API_KEY

    def __init__(self):
        headers = { "x-cg-demo-api-key": self._API_KEY }
        super().__init__(self._API_BASE_URL, headers)

    def get_coins_markets(self,
        vs: str = "usd",
        page: int = 1,
        limit: int = 250,
    ) -> List[Dict[str, Any]]:
        """Get list of coins with market data"""
        return self._send_request("/coins/markets", params = {
            "vs_currency": vs,
            "page": page,
            "per_page": limit,
            "order": "market_cap_desc",
            "sparkline": "false",
        }) or []


coingecko_client = CoinGeckoClient()