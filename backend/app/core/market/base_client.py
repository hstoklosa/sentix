from typing import Dict, Any, Optional, Callable
import requests
import logging
from datetime import datetime
import json

from app.core.market.cache import api_cache

logger = logging.getLogger(__name__)


class BaseApiClient:
    def __init__(self, api_base_url: str, headers: Dict[str, str]):
        self.api_base_url = api_base_url
        self.headers = headers
        
        # Default cache TTLs in seconds
        self.default_ttl = 300  # 5 minutes default
        self.endpoint_ttls = {}  # Override per endpoint

    def set_cache_ttl(self, endpoint: str, ttl_seconds: int) -> None:
        """
        Set custom TTL for specific endpoint
        
        Args:
            endpoint: API endpoint path
            ttl_seconds: Time-to-live in seconds
        """
        self.endpoint_ttls[endpoint] = ttl_seconds

    def _get_cache_ttl(self, endpoint: str) -> int:
        """Get TTL for endpoint, or default if not set"""
        return self.endpoint_ttls.get(endpoint, self.default_ttl)
    
    def _generate_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """Generate a unique cache key based on endpoint and params"""
        params_str = json.dumps(params, sort_keys=True) if params else ""
        return f"{self.api_base_url}{endpoint}:{params_str}"
    
    def _parse_next_update_time(self, response_data: Dict[str, Any]) -> Optional[int]:
        """
        Extract next update time from response data if available
        
        Returns:
            Seconds until next update or None if not available
        """
        # Default implementation - override in child classes if provider gives this info
        return None

    def _send_request(self, endpoint: str, params: dict = None, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Send HTTP GET request to API endpoint with caching
        
        Args:
            endpoint: API endpoint path
            params: Optional query parameters
            force_refresh: If True, bypass cache and force fresh data
            
        Returns:
            API response as dictionary or empty dict on failure
        """
        cache_key = self._generate_cache_key(endpoint, params)
        ttl = self._get_cache_ttl(endpoint)
        
        # If force refresh, delete from cache first
        if force_refresh:
            api_cache.delete(cache_key)
        
        # Use get_or_set to implement the cache-or-fetch pattern
        return api_cache.get_or_set(
            key=cache_key,
            ttl_seconds=ttl,
            fetch_func=lambda: self._fetch_from_api(endpoint, params)
        )
    
    def _fetch_from_api(self, endpoint: str, params: dict = None) -> Dict[str, Any]:
        """
        Fetch data directly from API without caching
        
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
            
            # Check if response contains next update time info and update TTL
            next_update_seconds = self._parse_next_update_time(result)
            if next_update_seconds is not None:
                cache_key = self._generate_cache_key(endpoint, params)
                # We already have data in cache, but update TTL based on provider info
                api_cache.set(cache_key, result, next_update_seconds)
                
            return result
        except requests.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return {} 