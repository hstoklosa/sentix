from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class NewsData(BaseModel):
    source: str = ""
    icon: str = ""
    feed: str = ""
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
        populate_by_name=True, # populate the model with field names
        strict=True, # fail fast on bad types
    )
