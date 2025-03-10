import logging

from fastapi import FastAPI
from sqlmodel import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.api.main import api_router
from app.core.db import create_db_and_tables, engine
from app.core.config import settings

logger = logging.getLogger(__name__)
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
        func=cleanup_expired_tokens,
        trigger=IntervalTrigger(hours=24),  # run once a day
        id="cleanup_expired_tokens",
        name="Remove expired tokens from database",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduled token cleanup task")

@app.on_event("shutdown")
def on_shutdown():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shut down")

async def cleanup_expired_tokens():
    """Remove expired tokens from the database"""
    try:
        from app.services.token import purge_expired_tokens
        
        with Session(engine) as session:
            removed_count = purge_expired_tokens(session=session)
            logger.info(f"Removed {removed_count} expired tokens from database")
    except Exception as e:
        logger.error(f"Error cleaning up expired tokens: {e}")

app.include_router(api_router, prefix=settings.API_BASE_PATH)