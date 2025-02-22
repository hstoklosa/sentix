from fastapi import FastAPI

from app.core.db import create_db_and_tables
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_BASE_PATH}/openapi.json",
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()