from typing import List, Dict, Any
import logging
import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


class CoinGeckoClient:
    _API_BASE_URL = "https://api.coingecko.com/api/v3"
    _API_KEY = settings.COINGECKO_API_KEY

    def __init__(self):
        self.headers = {
            "x-cg-demo-api-key": self._API_KEY,
        }

    def _send_request(self, url: str, params: dict = None) -> Dict[str, Any]:
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            return result
        except requests.RequestException as e:
            logger.error(f"CoinGecko API request failed: {str(e)}")
            return {}

    def get_coins_markets(self,
        vs: str = "usd",
        page: int = 1,
        limit: int = 250,
    ) -> List[Dict[str, Any]]:
        """Get list of coins with market data"""
        url = f"{self._API_BASE_URL}/coins/markets"
        params = {
            "vs_currency": vs,
            "page": page,
            "per_page": limit,
            "order": "market_cap_desc",
            "sparkline": "false",
        }
        return self._send_request(url, params) or []

coingecko_client = CoinGeckoClient()