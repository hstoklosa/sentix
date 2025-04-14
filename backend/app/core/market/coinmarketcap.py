from typing import Dict, Any
import requests
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class CoinMarketCapClient:
    _API_BASE_URL = "https://pro-api.coinmarketcap.com"
    _API_KEY = settings.COINMARKETCAP_API_KEY

    def __init__(self):
        self.headers = {
            "X-CMC_PRO_API_KEY": self._API_KEY,
        }

    def _send_request(self, url: str, params: dict = None) -> Dict[str, Any]:
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            return result
        except requests.RequestException as e:
            logger.error(f"CoinMarketCap API request failed: {str(e)}")
            return {}

    def get_market_stats(self) -> Dict[str, Any]:
        url = f"{self._API_BASE_URL}/v1/global-metrics/quotes/latest"
        return self._send_request(url)

    def get_fear_greed_index(self) -> Dict[str, Any]:
        url = f"{self._API_BASE_URL}/v3/fear-and-greed/latest"
        return self._send_request(url)
