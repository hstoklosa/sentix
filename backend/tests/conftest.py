import asyncio
import pytest
from typing import Generator, AsyncGenerator
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Import models to ensure they are registered with SQLModel
from app.models.user import User
from app.models.news import NewsItem, Coin, NewsCoin
from app.models.bookmark import NewsBookmark
from app.models.token import Token


# Synchronous in-memory SQLite for non-async tests
@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    with Session(db_engine) as session:
        yield session


# Async in-memory SQLite for async tests
@pytest.fixture
async def async_db_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
async def async_db_session(async_db_engine) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(async_db_engine) as session:
        yield session


# FastAPI test client
@pytest.fixture
def app():
    from app.main import app
    return app


@pytest.fixture
def client(app):
    with TestClient(app) as client:
        yield client


# Helper fixture to mock any HTTP client
@pytest.fixture
def mock_http_client(monkeypatch):
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code
            self.text = str(json_data)
            
        async def json(self):
            return self.json_data
            
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, *args):
            pass
            
    class MockHTTPClient:
        def __init__(self):
            self.responses = {}
            
        def set_response(self, url, json_data, status_code=200):
            self.responses[url] = MockResponse(json_data, status_code)
            
        async def get(self, url, *args, **kwargs):
            if url in self.responses:
                return self.responses[url]
            return MockResponse({}, 404)
            
        async def post(self, url, *args, **kwargs):
            if url in self.responses:
                return self.responses[url]
            return MockResponse({}, 404)
    
    mock_client = MockHTTPClient()
    
    import aiohttp
    monkeypatch.setattr(aiohttp, "ClientSession", lambda: mock_client)
    
    return mock_client


# Mock CoinGecko client for testing
@pytest.fixture
def mock_coingecko_client(monkeypatch):
    class MockCoinGeckoClient:
        async def get_coins_markets(self):
            return [
                {
                    "id": "bitcoin",
                    "symbol": "btc",
                    "name": "Bitcoin",
                    "image": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png",
                    "current_price": 50000,
                    "market_cap": 950000000000,
                    "market_cap_rank": 1,
                    "price_change_percentage_24h": 2.5,
                }
            ]
        
        async def get_coin_by_id(self, coin_id):
            if coin_id == "bitcoin":
                return {
                    "id": "bitcoin",
                    "symbol": "btc",
                    "name": "Bitcoin",
                    "image": {"large": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png"},
                    "market_data": {
                        "current_price": {"usd": 50000},
                        "market_cap": {"usd": 950000000000},
                    }
                }
            return None
    
    from app.core.market import coingecko
    monkeypatch.setattr(coingecko, "coingecko_client", MockCoinGeckoClient())
    return MockCoinGeckoClient()


# Test user data factory
@pytest.fixture
def user_factory():
    def create_user(username="testuser", email="test@example.com", password="password", is_superuser=False):
        from app.schemas.user import UserCreate
        return UserCreate(
            username=username,
            email=email,
            password=password,
            is_superuser=is_superuser
        )
    return create_user


# Test news data factory
@pytest.fixture
def news_data_factory():
    def create_news_data(
        title="Test News",
        body="This is a test news article",
        url="https://example.com/news/1",
        source="TestSource",
        coins=None
    ):
        from app.core.news.types import NewsData
        from datetime import datetime
        
        if coins is None:
            coins = ["BTC", "ETH"]
            
        return NewsData(
            title=title,
            body=body,
            url=url,
            image="https://example.com/image.jpg",
            icon="https://example.com/icon.png",
            time=datetime.utcnow(),
            source=source,
            feed="crypto",
            coins=coins
        )
    return create_news_data


# Test sentiment result factory
@pytest.fixture
def sentiment_factory():
    def create_sentiment(label="positive", score=0.85):
        return {
            "label": label,
            "score": score
        }
    return create_sentiment 