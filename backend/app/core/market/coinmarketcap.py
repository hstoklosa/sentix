from typing import Dict, Any
import logging

from app.core.config import settings
from app.core.market.base_client import BaseApiClient

logger = logging.getLogger(__name__)


class CoinMarketCapClient(BaseApiClient):
    _API_BASE_URL = "https://pro-api.coinmarketcap.com"
    _API_KEY = settings.COINMARKETCAP_API_KEY

    def __init__(self):
        headers = { "X-CMC_PRO_API_KEY": self._API_KEY }
        super().__init__(self._API_BASE_URL, headers)

    def get_market_stats(self) -> Dict[str, Any]:
        return self._send_request("/v1/global-metrics/quotes/latest")

    def get_fear_greed_index(self) -> Dict[str, Any]:
        return self._send_request("/v3/fear-and-greed/latest")


cmc_client = CoinMarketCapClient()