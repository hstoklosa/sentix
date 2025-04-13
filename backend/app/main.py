from fastapi import FastAPI

from starlette.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.api.main import api_router
from app.core.db import create_db_and_tables
from app.services.token import purge_expired_tokens
from app.services.coin import sync_coins_from_coingecko
from app.ml_models import cryptobert
from app.core.config import settings
from app.utils import setup_logger

logger = setup_logger()
scheduler = AsyncIOScheduler()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_BASE_PATH}/openapi.json",
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    sync_coins_from_coingecko()

    # Load the sentiment analyser
    cryptobert.load_model()

    # Schedule token cleanup task
    scheduler.add_job(
        id="cleanup_expired_tokens",
        name="Remove expired tokens from database",
        func=purge_expired_tokens,
        trigger=IntervalTrigger(hours=24),  # run once a day
        replace_existing=True,
    )
    
    # Schedule regular coin synchronisation task
    scheduler.add_job(
        id="sync_coins",
        name="Synchronise coins from CoinGecko",
        func=sync_coins_from_coingecko,
        trigger=IntervalTrigger(hours=12),  # run twice a day
        replace_existing=True,
    )
    
    scheduler.start()


@app.on_event("shutdown")
def on_shutdown():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shut down")


if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_BASE_PATH)