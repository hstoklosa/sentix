from app.api.routes.websocket import news as news_websocket
from app.api.routes.rest import auth as auth_rest

__all__ = ["news_websocket", "auth_rest"]