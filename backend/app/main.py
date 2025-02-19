from typing import Union
from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    openapi_url=f"{settings.API_VERSION}/openapi.json",
)
