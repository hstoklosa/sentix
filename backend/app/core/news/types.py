from datetime import datetime, timezone

class NewsData():
    title: str
    link: str
    body: str
    image: str
    is_quote: bool
    quote_message: str
    quote_user: str
    quote_image: str
    is_reply: bool
    is_self_reply: bool
    reply_user: str
    reply_message: str
    reply_image: str
    is_retweet: bool
    retweet_user: str
    icon: str
    source: str
    time: datetime
    coin: set[str]
    feed: str
    sfx: str
    ignored: bool