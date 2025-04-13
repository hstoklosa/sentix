import logging
from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.core.db import engine
from app.models.token import Token
from app.core.security import decode_token, verify_token_type

logger = logging.getLogger(__name__)


def blacklist_token(*, session: Session, token: str) -> None:
    """Add a refresh token to the blacklist"""
    payload = decode_token(token)
    if not payload or not verify_token_type(payload, "refresh"):
        return
    
    jti, exp = payload.get("jti"), payload.get("exp")
    if not jti or not exp:
        return
    
    if is_token_blacklisted(session=session, jti=jti):
        return
    
    # Create blacklisted entry
    token_entry = Token(
        jti=jti,
        is_blacklisted=True,
        expires_at=datetime.fromtimestamp(exp),
    )
    
    session.add(token_entry)
    session.commit()


def is_token_blacklisted(*, session: Session, jti: str) -> bool:
    """Check if a token is blacklisted by its JTI"""
    stmt = select(Token).where(Token.jti == jti, Token.is_blacklisted == True)
    result = session.exec(stmt).first()
    return result is not None


def get_token_by_jti(*, session: Session, jti: str) -> Optional[Token]:
    """Get a token by its JTI"""
    stmt = select(Token).where(Token.jti == jti)
    return session.exec(stmt).first()


def get_expired_tokens(*, session: Session) -> list[Token]:
    """Get expired tokens from the database"""
    now = datetime.utcnow()
    stmt = select(Token).where(Token.expires_at < now)
    return session.exec(stmt).all() or []


def purge_expired_tokens() -> int:
    """Remove expired tokens from the database to prevent table size buildup"""
    try:
        with Session(engine) as session: 
            expired_tokens = get_expired_tokens(session=session)
            
            count = 0
            for token in expired_tokens:
                session.delete(token)
                count += 1
            
            if count > 0:
                session.commit()
            
            logger.info(f"Removed {count} expired tokens from database")
    except Exception as e:
        logger.error(f"Error cleaning up expired tokens: {e}") 
