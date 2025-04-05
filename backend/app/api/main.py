from fastapi import APIRouter
from app.api.routes import auth_rest, news_rest, news_websocket
# from app.api.routes import auth_rest, news_websocket

api_router = APIRouter()

api_router.include_router(auth_rest.router)
api_router.include_router(news_rest.router)
api_router.include_router(news_websocket.router)
