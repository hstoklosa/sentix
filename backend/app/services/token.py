import logging
from datetime import datetime
from typing import Optional

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import sessionmanager
from app.models.token import Token
from app.core.security import decode_token, verify_token_type

logger = logging.getLogger(__name__)


async def blacklist_token(*, session: AsyncSession, token: str) -> None:
    """Add a refresh token to the blacklist"""
    payload = decode_token(token)
    if not payload or not verify_token_type(payload, "refresh"):
        return
    
    jti, exp = payload.get("jti"), payload.get("exp")
    if not jti or not exp:
        return
    
    if await is_token_blacklisted(session=session, jti=jti):
        return
    
    # Create blacklisted entry
    token_entry = Token(
        jti=jti,
        is_blacklisted=True,
        expires_at=datetime.fromtimestamp(exp),
    )
    
    session.add(token_entry)
    await session.commit()
    await session.refresh(token_entry)


async def is_token_blacklisted(*, session: AsyncSession, jti: str) -> bool:
    """Check if a token is blacklisted by its JTI"""
    stmt = select(Token).where(Token.jti == jti, Token.is_blacklisted == True)
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def get_token_by_jti(*, session: AsyncSession, jti: str) -> Optional[Token]:
    """Get a token by its JTI"""
    stmt = select(Token).where(Token.jti == jti)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_expired_tokens(*, session: AsyncSession) -> list[Token]:
    """Get expired tokens from the database"""
    now = datetime.utcnow()
    stmt = select(Token).where(Token.expires_at < now)
    result = await session.execute(stmt)
    return result.scalars().all() or []


async def purge_expired_tokens() -> int:
    """Remove expired tokens from the database to prevent table size buildup"""
    try:
        async with sessionmanager.session() as session: 
            expired_tokens = await get_expired_tokens(session=session)
            
            count = 0
            for token in expired_tokens:
                await session.delete(token)
                count += 1
            
            if count > 0:
                await session.commit()
            
            logger.info(f"Removed {count} expired tokens from database")
            return count
    except Exception as e:
        logger.error(f"Error cleaning up expired tokens: {e}")
        return 0 