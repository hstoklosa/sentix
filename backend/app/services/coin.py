import logging

from sqlmodel import Session

from app.core.db import engine
from app.core.coingecko.client import CoinGeckoClient
from app.models.coin import Coin

logger = logging.getLogger(__name__)


def sync_coins_from_coingecko():
    """Sync coins from CoinGecko API to database"""
    client = CoinGeckoClient()
    coins_list = client.get_coins_markets(limit=5)
    
    if not coins_list:
        logger.error("Failed to fetch coins list from CoinGecko API")
        return
    
    logger.info(f"Fetched {len(coins_list)} coins from CoinGecko")
    
    with Session(engine) as session:
        for coin_data in coins_list:
            try:
                coin_id = coin_data.get("id")
                symbol = coin_data.get("symbol", "").upper()
                name = coin_data.get("name", "")
                image_url = coin_data.get("image", "")
                
                if not coin_id or not symbol or not name or not image_url:
                    continue
                
                new_coin = Coin(
                    symbol=symbol,
                    name=name,
                    image_url=image_url
                )
                session.add(new_coin)
            except Exception as e:
                logger.error(f"Error processing coin {coin_data.get('symbol')}: {str(e)}")
                continue
        
        session.commit()
    
    logger.info("Coin synchronisation completed") 