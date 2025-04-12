from fastapi import FastAPI

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.db import create_db_and_tables
from app.services.token import cleanup_expired_tokens
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
    
    # Schedule token cleanup task
    scheduler.add_job(
        id="cleanup_expired_tokens",
        name="Remove expired tokens from database",
        func=cleanup_expired_tokens,
        trigger=IntervalTrigger(hours=24),  # run once a day
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