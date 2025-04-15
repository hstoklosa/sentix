from typing import Dict, Any, Optional, Callable, TypeVar, Generic
from datetime import datetime, timedelta
import logging
import threading

T = TypeVar('T')

logger = logging.getLogger(__name__)


class CachedResponse(Generic[T]):
    """Class to store cached response with expiration time."""
    
    def __init__(self, data: T, ttl_seconds: int):
        self.data = data
        self.expiry_time = datetime.now() + timedelta(seconds=ttl_seconds)
    
    def is_expired(self) -> bool:
        """Check if the cached response has expired."""
        return datetime.now() > self.expiry_time
    
    @property
    def seconds_until_expiry(self) -> int:
        """Get seconds remaining until cache expiry."""
        if self.is_expired():
            return 0
        delta = self.expiry_time - datetime.now()
        return max(0, int(delta.total_seconds()))


class ApiCache:
    """
    Cache manager for API responses.
    Implements a simple in-memory cache with TTL (time-to-live) functionality.
    """
    
    def __init__(self):
        self._cache: Dict[str, CachedResponse] = {}
        self._lock = threading.RLock()  # Reentrant lock for thread safety
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache if it exists and is not expired.
        
        Args:
            key: The cache key
            
        Returns:
            The cached data or None if not in cache or expired
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            cached_response = self._cache[key]
            if cached_response.is_expired():
                # Clean up expired items
                del self._cache[key]
                return None
                
            return cached_response.data
    
    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """
        Store a value in the cache with a specified TTL.
        
        Args:
            key: The cache key
            value: The data to cache
            ttl_seconds: Time-to-live in seconds
        """
        with self._lock:
            cached_response = CachedResponse(value, ttl_seconds)
            self._cache[key] = cached_response
            
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def get_or_set(self, key: str, ttl_seconds: int, fetch_func: Callable[[], T]) -> T:
        """
        Get value from cache or execute fetch function if not available.
        
        Args:
            key: The cache key
            ttl_seconds: Time-to-live in seconds
            fetch_func: Function to call if value is not in cache
            
        Returns:
            The cached or newly fetched data
        """
        with self._lock:
            cached_data = self.get(key)
            if cached_data is not None:
                logger.debug(f"Cache hit for key '{key}'")
                return cached_data
                
            logger.debug(f"Cache miss for key '{key}', fetching data")
            fresh_data = fetch_func()
            
            # Only cache if we got valid data
            if fresh_data:
                self.set(key, fresh_data, ttl_seconds)
                
            return fresh_data
    
    def get_expiry_time(self, key: str) -> Optional[int]:
        """
        Get seconds until cache expiry for a key.
        
        Args:
            key: The cache key
            
        Returns:
            Seconds until expiry or None if key not in cache
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            return self._cache[key].seconds_until_expiry

# Global cache instance
api_cache = ApiCache() 