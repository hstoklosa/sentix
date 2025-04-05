from app.api.routes.websocket import news as news_websocket
from app.api.routes.rest import (
    auth as auth_rest,
    news as news_rest
)

__all__ = ["auth_rest", "news_rest", "news_websocket"]
