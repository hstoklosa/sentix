from datetime import datetime, timezone

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