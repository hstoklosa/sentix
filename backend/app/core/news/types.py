from datetime import datetime
from typing import Protocol, Callable, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, model_validator

class DataSource(str, Enum):
    TREE_NEWS = "TreeNews"
    COINDESK = "CoinDesk"

class NewsData(BaseModel):
    """Immutable news data structure with validation."""
    source: str = ""
    icon: str = ""
    feed: DataSource = DataSource.TREE_NEWS
    url: str = ""
    title: str = ""
    body: str = ""
    image: str = ""
    time: datetime = Field(default_factory=datetime.utcnow)
    is_reply: bool = False
    is_self_reply: bool = False
    is_quote: bool = False
    is_retweet: bool = False
    coins: set[str] = Field(default_factory=set)

    model_config = ConfigDict(
        # frozen=True,    # make instances immutable
        populate_by_name=True,
        strict=True,    # fail fast on bad types
    )


class ProviderStatus(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RETRYING = "retrying"


class NewsProvider(Protocol):
    """Protocol defining the interface for news providers."""
    
    @property
    def name(self) -> str:
        """Provider name identifier"""
        ...

    @property
    def status(self) -> ProviderStatus:
        """Current connection status"""
        ...

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