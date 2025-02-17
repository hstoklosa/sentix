from typing import Union
from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    openapi_url=f"{settings.API_VERSION}/openapi.json",
)

@app.get("/")
def read_root():
    return { "API_NAME": settings.API_VERSION }

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return { "item_id": item_id, "q": q }