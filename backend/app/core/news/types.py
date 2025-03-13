from datetime import datetime, timezone

class NewsData():
    source: str
    icon: str
    feed: str
    link: str
    title: str
    body: str
    image: str
    time: datetime
    is_reply: bool
    is_self_reply: bool
    is_quote: bool
    is_retweet: bool
    coin: set[str]
    quote_message: str
    quote_user: str
    quote_image: str
    reply_user: str
    reply_message: str
    reply_image: str
    retweet_user: str

    ignored: bool