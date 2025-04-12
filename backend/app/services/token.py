import logging
from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.models.token import Token
from app.core.security import decode_token
from app.core.db import engine

logger = logging.getLogger(__name__)


def blacklist_token(*, session: Session, token: str) -> None:
    """Add a refresh token to the blacklist"""
    try:
        # Decode the token to get its payload
        payload = decode_token(token)
        
        # Only blacklist refresh tokens
        if payload.get("type") != "refresh":
            return
        
        # Extract token data
        jti = payload.get("jti")
        exp = payload.get("exp")
        
        if not jti or not exp:
            return
        
        # Convert exp timestamp to datetime
        expires_at = datetime.fromtimestamp(exp)
        
        # Check if token is already blacklisted
        stmt = select(Token).where(Token.jti == jti)
        existing = session.exec(stmt).first()
        
        if existing:
            return
        
        # Create blacklist entry
        token_entry = Token(
            jti=jti,
            expires_at=expires_at,
            is_blacklisted=True
        )
        
        session.add(token_entry)
        session.commit()
    except Exception:
        # If token is invalid or any other error occurs, no need to blacklist
        pass


def is_token_blacklisted(*, session: Session, jti: str) -> bool:
    """Check if a token is blacklisted by its JTI"""
    stmt = select(Token).where(Token.jti == jti, Token.is_blacklisted == True)
    result = session.exec(stmt).first()
    return result is not None


def get_token_by_jti(*, session: Session, jti: str) -> Optional[Token]:
    """Get a token by its JTI"""
    stmt = select(Token).where(Token.jti == jti)
    return session.exec(stmt).first()


def purge_expired_tokens(*, session: Session) -> int:
    """Remove expired tokens from the database to keep the table size manageable
    
    Returns:
        int: Number of tokens removed
    """
    now = datetime.utcnow()
    stmt = select(Token).where(Token.expires_at < now)
    expired_tokens = session.exec(stmt).all()
    
    count = 0
    for token in expired_tokens:
        session.delete(token)
        count += 1
    
    if count > 0:
        session.commit()
    
    return count


async def cleanup_expired_tokens():
    """Scheduled task to remove expired tokens from the database"""
    try:
        with Session(engine) as session:
            removed_count = purge_expired_tokens(session=session)
            logger.info(f"Removed {removed_count} expired tokens from database")
    except Exception as e:
        logger.error(f"Error cleaning up expired tokens: {e}") 