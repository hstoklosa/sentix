"""
News module for fetching and processing news data
"""

from app.core.news.tree_news import TreeNews
from app.core.news.types import NewsData
from app.core.news.news_manager import NewsIngestionService
from app.core.news.websocket_manager import ConnectionManager

__all__ = ["TreeNews", "NewsData", "NewsIngestionService", "ConnectionManager"]
