from fastapi import FastAPI
from contextlib import asynccontextmanager

from starlette.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.api.main import api_router
from app.core.database import create_db_and_tables
from app.services.token import purge_expired_tokens
from app.services.coin import sync_coins_from_coingecko
from app.core.config import settings
from app.utils import setup_logger
from app.core.news.websocket_manager import connection_manager
from app.core.news.news_manager import NewsIngestionService

logger = setup_logger()
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Function that handles the startup and shutdown events."""
    await create_db_and_tables()
    await sync_coins_from_coingecko()

    news_service = NewsIngestionService(connection_manager)
    await news_service.initialize()

    scheduler.add_job(
        id="cleanup_expired_tokens",
        name="Remove expired tokens from database",
        func=purge_expired_tokens,
        trigger=IntervalTrigger(hours=24),
        replace_existing=True,
    )
    
    scheduler.add_job(
        id="sync_coins",
        name="Synchronise coins from CoinGecko",
        func=sync_coins_from_coingecko,
        trigger=IntervalTrigger(hours=12),
        replace_existing=True,
    )
    
    scheduler.start()

    try:
        yield
    finally:
        if news_service and news_service.is_initialized:
            await news_service.shutdown()

        if scheduler.running:
            scheduler.shutdown()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_BASE_PATH}/openapi.json",
    lifespan=lifespan,
)


if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.include_router(api_router, prefix=settings.API_BASE_PATH)
