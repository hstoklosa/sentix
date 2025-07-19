from typing import Dict, Any, Optional
import logging
import json

from aiocache import Cache
from aiocache.serializers import JsonSerializer
import asyncio
import aiohttp

logger = logging.getLogger(__name__)
api_cache = Cache.MEMORY(serializer=JsonSerializer())


class BaseApiClient:
    def __init__(self, api_base_url: str, headers: Dict[str, str]):
        self.api_base_url = api_base_url
        self.headers = headers        
        self.default_ttl = 300   # 5 minutes default
        self.endpoint_ttls = {}  # override per endpoint

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
        # Default implementation - can be overridden in subclasses if provider gives this info
        return None

    async def _send_request(self, endpoint: str, params: dict = None, force_refresh: bool = False) -> Dict[str, Any]:
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
            await api_cache.delete(cache_key)
        
        # Try to get from cache first
        cached_data = await api_cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Cache hit for key '{cache_key}'")
            return cached_data
        
        logger.info(f"Cache miss for key '{cache_key}', fetching data")
        fresh_data = await self._fetch_from_api(endpoint, params)
        
        # Only cache if we got valid data
        if fresh_data:
            await api_cache.set(cache_key, fresh_data, ttl=ttl)
        
        return fresh_data
    
    async def _fetch_from_api(self, endpoint: str, params: dict = None) -> Dict[str, Any]:
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
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, params=params, timeout=10) as response:
                    response.raise_for_status()
                    result = await response.json()
                    
                    # Check if response contains next update time info and update TTL
                    next_update_seconds = self._parse_next_update_time(result)
                    if next_update_seconds is not None:
                        cache_key = self._generate_cache_key(endpoint, params)
                        # We already have data in cache, but update TTL based on provider info
                        await api_cache.set(cache_key, result, ttl=next_update_seconds)
                        
                    return result
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"API request failed: {str(e)}")
            return {} 