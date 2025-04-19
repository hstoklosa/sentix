from datetime import datetime, timezone
from typing import Protocol, Callable, Any

class NewsData():
    source: str
    icon: str
    feed: str
    url: str
    title: str
    body: str
    image: str
    time: datetime
    is_reply: bool
    is_self_reply: bool
    is_quote: bool
    is_retweet: bool
    coins: set[str]

class NewsProvider(Protocol):
    """Protocol defining the interface for news providers."""
    
    async def connect(self, callback: Callable[[NewsData], Any]) -> None:
        """
        Connect to the news provider's data source.
        
        Args:
            callback: Function to call when news is received
        """
        ...
    
    async def disconnect(self) -> None:
        """Disconnect from the news provider's data source."""
        ...