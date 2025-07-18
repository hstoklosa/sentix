import json
import logging

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.news.types import NewsData

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
)


async def analyse_post_sentiment(post: NewsData) -> dict:
    """
    Analyse the sentiment of a news post using OpenAI's API.
    
    Returns:
        dict with "label" (positive/negative/neutral) and "score" (0-1).
    """
    try:
        prompt = f"""Analyse the sentiment of this cryptocurrency news post. Consider both title and content.

        Title: {post.title}
        Content: {post.body}

        Determine if the sentiment is positive, negative, or neutral. Respond in JSON format only with two fields:
        1. "label": Either "positive", "negative", or "neutral"
        2. "score": A confidence score between 0 and 1

        Example response:
        {{"label": "positive", "score": 0.85}}"""

        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a cryptocurrency expert that analyses the sentiment of news articles. Respond only in the exact JSON format requested."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        result = response.choices[0].message.content
        return json.loads(result)

    except Exception as e:
        logger.error(f"Error analysing sentiment for post {post.title[:50]}: {e}")
        return {
            "label": "neutral",
            "score": 0.5,
        }
