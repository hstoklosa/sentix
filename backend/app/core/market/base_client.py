from typing import Dict, Any
import requests
import logging

logger = logging.getLogger(__name__)


class BaseApiClient:
    def __init__(self, api_base_url: str, headers: Dict[str, str]):
        self.api_base_url = api_base_url
        self.headers = headers

    def _send_request(self, endpoint: str, params: dict = None) -> Dict[str, Any]:
        """
        Send HTTP GET request to API endpoint
        
        Args:
            endpoint: API endpoint path
            params: Optional query parameters
            
        Returns:
            API response as dictionary or empty dict on failure
        """
        url = f"{self.api_base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            return result
        except requests.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return {} 