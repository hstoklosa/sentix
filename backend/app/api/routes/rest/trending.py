import math

from fastapi import APIRouter, Depends

from app.deps import AsyncSessionDep, CurrentUserDep
from app.models.user import User
from app.services.coin import get_trending_coins_by_mentions
from app.schemas.coin import TrendingCoinsResponse, TrendingCoin, SentimentStats
from app.schemas.pagination import PaginationParams

router = APIRouter(
    prefix="/trending",
    tags=["trending"]
)


@router.get("/coins", response_model=TrendingCoinsResponse)
async def get_trending_coins(
    session: AsyncSessionDep,
    current_user: CurrentUserDep,
    pagination: PaginationParams = Depends(),
) -> TrendingCoinsResponse:
    """Get paginated list of trending coins based on mentions in today's posts"""
    trending_coins, total_count = await get_trending_coins_by_mentions(
        session=session, 
        page=pagination.page,
        page_size=pagination.page_size
    )
    
    # Calculate pagination metadata
    total_pages = math.ceil(total_count / pagination.page_size) if total_count > 0 else 0
    has_next = pagination.page < total_pages
    has_prev = pagination.page > 1
    
    # Transform dicts to schema objects
    coin_items = []
    for item in trending_coins:
        sentiment_stats = SentimentStats(
            positive=item["sentiment_stats"]["positive"],
            negative=item["sentiment_stats"]["negative"],
            neutral=item["sentiment_stats"]["neutral"]
        )
        
        coin = TrendingCoin(
            id=item["id"],
            symbol=item["symbol"],
            name=item["name"],
            image_url=item["image_url"],
            mention_count=item["mention_count"],
            sentiment_stats=sentiment_stats
        )
        coin_items.append(coin)

    return TrendingCoinsResponse(
        page=pagination.page,
        page_size=pagination.page_size,
        total=total_count,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev,
        items=coin_items
    ) 