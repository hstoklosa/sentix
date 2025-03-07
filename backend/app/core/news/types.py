from datetime import datetime, timezone

class NewsData():
    title: str
    link: str
    body: str
    image: str
    source: str
    time: datetime
    coin: set[str]