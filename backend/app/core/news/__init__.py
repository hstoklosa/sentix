"""
News module for fetching and processing news data
"""

from app.core.news.tree_news import TreeNews
from app.core.news.types import NewsData, NewsProvider
from app.core.news.news_manager import NewsManager

__all__ = ["TreeNews", "NewsData", "NewsManager", "NewsProvider"] 