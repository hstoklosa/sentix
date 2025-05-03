import pytest
from datetime import datetime, date, time
from sqlmodel import select, Session
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.coin import get_trending_coins_by_mentions, async_sync_coins_from_coingecko
from app.models.coin import Coin
from app.models.news import NewsItem, NewsCoin


@pytest.mark.asyncio
async def test_get_trending_coins_by_mentions(async_db_session):
    """Test retrieving trending coins by mentions for the current day"""
    # Arrange
    # Create test coins
    coin1 = Coin(symbol="BTC", name="Bitcoin", image_url="https://example.com/btc.png")
    coin2 = Coin(symbol="ETH", name="Ethereum", image_url="https://example.com/eth.png")
    coin3 = Coin(symbol="SOL", name="Solana", image_url="https://example.com/sol.png")
    async_db_session.add(coin1)
    async_db_session.add(coin2)
    async_db_session.add(coin3)
    await async_db_session.commit()
    
    # Refresh to get IDs
    await async_db_session.refresh(coin1)
    await async_db_session.refresh(coin2)
    await async_db_session.refresh(coin3)
    
    # Create test news items for today
    today = date.today()
    start_of_day = datetime.combine(today, time.min)
    
    # Create news items with different sentiments
    news1 = NewsItem(
        title="Bitcoin news",
        body="Bitcoin is going up",
        url="https://example.com/news/btc1",
        source="TestSource",
        feed="crypto",
        time=start_of_day,
        image_url="https://example.com/image1.jpg",
        sentiment="Bullish"
    )
    news2 = NewsItem(
        title="Bitcoin news 2",
        body="Bitcoin is going down",
        url="https://example.com/news/btc2",
        source="TestSource",
        feed="crypto",
        time=start_of_day,
        image_url="https://example.com/image2.jpg",
        sentiment="Bearish"
    )
    news3 = NewsItem(
        title="Ethereum news",
        body="Ethereum is stable",
        url="https://example.com/news/eth1",
        source="TestSource",
        feed="crypto",
        time=start_of_day,
        image_url="https://example.com/image3.jpg",
        sentiment="Neutral"
    )
    
    async_db_session.add(news1)
    async_db_session.add(news2)
    async_db_session.add(news3)
    await async_db_session.commit()
    
    # Refresh to get IDs
    await async_db_session.refresh(news1)
    await async_db_session.refresh(news2)
    await async_db_session.refresh(news3)
    
    # Create coin-news associations
    news_coin1 = NewsCoin(coin_id=coin1.id, news_item_id=news1.id)
    news_coin2 = NewsCoin(coin_id=coin1.id, news_item_id=news2.id)
    news_coin3 = NewsCoin(coin_id=coin2.id, news_item_id=news3.id)
    
    async_db_session.add(news_coin1)
    async_db_session.add(news_coin2)
    async_db_session.add(news_coin3)
    await async_db_session.commit()
    
    # Act
    trending_coins, total_count = await get_trending_coins_by_mentions(async_db_session)
    
    # Assert
    assert total_count == 2  # Two coins mentioned today
    assert len(trending_coins) == 2
    
    # Bitcoin should be first with 2 mentions
    assert trending_coins[0]["id"] == coin1.id
    assert trending_coins[0]["symbol"] == "BTC"
    assert trending_coins[0]["mention_count"] == 2
    assert trending_coins[0]["sentiment_stats"]["positive"] == 1  # Bullish
    assert trending_coins[0]["sentiment_stats"]["negative"] == 1  # Bearish
    assert trending_coins[0]["sentiment_stats"]["neutral"] == 0
    
    # Ethereum should be second with 1 mention
    assert trending_coins[1]["id"] == coin2.id
    assert trending_coins[1]["symbol"] == "ETH"
    assert trending_coins[1]["mention_count"] == 1
    assert trending_coins[1]["sentiment_stats"]["positive"] == 0
    assert trending_coins[1]["sentiment_stats"]["negative"] == 0
    assert trending_coins[1]["sentiment_stats"]["neutral"] == 1


@pytest.mark.asyncio
async def test_get_trending_coins_by_mentions_pagination(async_db_session):
    """Test pagination for trending coins"""
    # Arrange
    # Create 5 test coins
    coins = []
    for i in range(5):
        coin = Coin(
            symbol=f"COIN{i}",
            name=f"Coin {i}",
            image_url=f"https://example.com/coin{i}.png"
        )
        async_db_session.add(coin)
        coins.append(coin)
    
    await async_db_session.commit()
    
    # Refresh to get IDs
    for coin in coins:
        await async_db_session.refresh(coin)
    
    # Create a news item for each coin for today
    today = date.today()
    start_of_day = datetime.combine(today, time.min)
    
    news_items = []
    for i, coin in enumerate(coins):
        news = NewsItem(
            title=f"News about {coin.name}",
            body=f"This is news about {coin.name}",
            url=f"https://example.com/news/{i}",
            source="TestSource",
            feed="crypto",
            time=start_of_day,
            image_url=f"https://example.com/image{i}.jpg",
            sentiment="Neutral"
        )
        async_db_session.add(news)
        news_items.append(news)
    
    await async_db_session.commit()
    
    # Refresh to get IDs
    for news in news_items:
        await async_db_session.refresh(news)
    
    # Create coin-news associations with different mention counts
    # COIN0 has 5 mentions, COIN1 has 4 mentions, etc.
    for i, coin in enumerate(coins):
        for j in range(5-i):  # Creates 5, 4, 3, 2, 1 mentions respectively
            news_coin = NewsCoin(coin_id=coin.id, news_item_id=news_items[0].id)  # Use the same news item for simplicity
            async_db_session.add(news_coin)
    
    await async_db_session.commit()
    
    # Act - Get first page (2 items)
    trending_page1, total_count = await get_trending_coins_by_mentions(
        async_db_session, page=1, page_size=2
    )
    
    # Act - Get second page (2 items)
    trending_page2, _ = await get_trending_coins_by_mentions(
        async_db_session, page=2, page_size=2
    )
    
    # Act - Get third page (1 item)
    trending_page3, _ = await get_trending_coins_by_mentions(
        async_db_session, page=3, page_size=2
    )
    
    # Assert
    assert total_count == 5
    
    # Check first page
    assert len(trending_page1) == 2
    assert trending_page1[0]["symbol"] == "COIN0"
    assert trending_page1[0]["mention_count"] == 5
    assert trending_page1[1]["symbol"] == "COIN1"
    assert trending_page1[1]["mention_count"] == 4
    
    # Check second page
    assert len(trending_page2) == 2
    assert trending_page2[0]["symbol"] == "COIN2"
    assert trending_page2[0]["mention_count"] == 3
    assert trending_page2[1]["symbol"] == "COIN3"
    assert trending_page2[1]["mention_count"] == 2
    
    # Check third page
    assert len(trending_page3) == 1
    assert trending_page3[0]["symbol"] == "COIN4"
    assert trending_page3[0]["mention_count"] == 1


@pytest.mark.asyncio
async def test_get_trending_coins_empty_result(async_db_session):
    """Test retrieving trending coins when there are no mentions today"""
    # Act
    trending_coins, total_count = await get_trending_coins_by_mentions(async_db_session)
    
    # Assert
    assert total_count == 0
    assert len(trending_coins) == 0


@pytest.mark.asyncio
async def test_async_sync_coins_from_coingecko(async_db_session, mock_coingecko_client):
    """Test synchronizing coins from CoinGecko API"""
    # Arrange
    # The mock_coingecko_client fixture already sets up a mock that returns a predefined list
    
    # Act
    await async_sync_coins_from_coingecko()
    
    # Assert - Check that the coin was added to the database
    statement = select(Coin).where(Coin.symbol == "BTC")
    result = await async_db_session.exec(statement)
    coin = result.first()
    
    assert coin is not None
    assert coin.symbol == "BTC"
    assert coin.name == "Bitcoin"
    assert coin.image_url == "https://assets.coingecko.com/coins/images/1/large/bitcoin.png"


@pytest.mark.asyncio
async def test_async_sync_coins_update_existing(async_db_session, mock_coingecko_client):
    """Test that existing coins are updated rather than duplicated"""
    # Arrange - Add an existing coin with the same symbol but different name/image
    existing_coin = Coin(
        symbol="BTC",
        name="Old Bitcoin Name",
        image_url="https://old-url.com/btc.png"
    )
    async_db_session.add(existing_coin)
    await async_db_session.commit()
    
    # Act
    await async_sync_coins_from_coingecko()
    
    # Assert - Check that the coin was updated, not duplicated
    statement = select(Coin).where(Coin.symbol == "BTC")
    result = await async_db_session.exec(statement)
    coins = result.all()
    
    # Should only be one coin with this symbol
    assert len(coins) == 1
    
    # The coin details should be updated to match the CoinGecko data
    assert coins[0].name == "Bitcoin"
    assert coins[0].image_url == "https://assets.coingecko.com/coins/images/1/large/bitcoin.png"


@pytest.mark.asyncio
async def test_async_sync_coins_handles_errors(async_db_session):
    """Test that sync function handles errors gracefully"""
    # Arrange - Create a mock client that raises an exception
    with patch('app.core.market.coingecko.CoinGeckoClient') as MockClient:
        # The get_coins_markets method raises an exception
        mock_instance = AsyncMock()
        mock_instance.get_coins_markets.side_effect = Exception("API Error")
        MockClient.return_value = mock_instance
        
        # Act - Should not raise an exception
        await async_sync_coins_from_coingecko()
        
        # Assert
        # Function should have been called
        assert mock_instance.get_coins_markets.called
        # No coins should have been added
        statement = select(Coin)
        result = await async_db_session.exec(statement)
        coins = result.all()
        assert len(coins) == 0


@pytest.mark.asyncio
async def test_async_sync_coins_handles_empty_response(async_db_session):
    """Test that sync function handles empty API response"""
    # Arrange - Create a mock client that returns None
    with patch('app.core.market.coingecko.CoinGeckoClient') as MockClient:
        mock_instance = AsyncMock()
        mock_instance.get_coins_markets.return_value = None
        MockClient.return_value = mock_instance
        
        # Act
        await async_sync_coins_from_coingecko()
        
        # Assert
        # Function should have been called
        assert mock_instance.get_coins_markets.called
        # No coins should have been added
        statement = select(Coin)
        result = await async_db_session.exec(statement)
        coins = result.all()
        assert len(coins) == 0


def test_sync_coins_from_coingecko():
    """Test the synchronous wrapper for coin synchronization"""
    # This test verifies that the synchronous wrapper function calls the async function
    with patch('app.services.coin.asyncio.run') as mock_run:
        from app.services.coin import sync_coins_from_coingecko
        
        # Act
        sync_coins_from_coingecko()
        
        # Assert
        mock_run.assert_called_once()
        # The first argument should be the coroutine object from async_sync_coins_from_coingecko
        args, _ = mock_run.call_args
        assert 'async_sync_coins_from_coingecko' in str(args[0]) 