from fastapi import APIRouter
from app.api.routes import auth_rest, news_rest, news_websocket, bookmark_rest, market_rest, trending_rest

api_router = APIRouter()

api_router.include_router(auth_rest.router)
api_router.include_router(news_rest.router)
api_router.include_router(bookmark_rest.router)
api_router.include_router(news_websocket.router)
api_router.include_router(market_rest.router)
api_router.include_router(trending_rest.router)