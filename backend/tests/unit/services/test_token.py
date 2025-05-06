import pytest
from datetime import datetime, timedelta
from sqlmodel import Session
import uuid
from unittest.mock import patch, MagicMock

from app.services.token import (
    blacklist_token,
    get_token_by_jti,
    is_token_blacklisted,
    get_expired_tokens,
    purge_expired_tokens
)
from app.models.token import Token
from app.core.config import settings
from app.core.security import create_refresh_token

class TestTokenService:
    """Unit tests for the token service module"""
    
    def test_get_token_by_jti(self, db_session: Session):
        """Test retrieving a token by JTI"""
        # Arrange
        jti = "test-jti"
        expires_at = datetime.utcnow() + timedelta(days=30)
        token = Token(jti=jti, is_blacklisted=False, expires_at=expires_at)
        db_session.add(token)
        db_session.commit()
        
        # Act
        found_token = get_token_by_jti(session=db_session, jti=jti)
        
        # Assert
        assert found_token is not None
        assert found_token.jti == jti
        assert found_token.is_blacklisted is False
        
    def test_get_token_by_jti_nonexistent(self, db_session: Session):
        """Test retrieving a nonexistent token returns None"""
        # Act
        token = get_token_by_jti(session=db_session, jti="nonexistent_jti")
        
        # Assert
        assert token is None
    
    def test_is_token_blacklisted_when_not_blacklisted(self, db_session: Session):
        """Test checking if a token is blacklisted when it's not"""
        # Arrange
        jti = "test-jti"
        expires_at = datetime.utcnow() + timedelta(days=30)
        token = Token(jti=jti, is_blacklisted=False, expires_at=expires_at)
        db_session.add(token)
        db_session.commit()
        
        # Act
        result = is_token_blacklisted(session=db_session, jti=jti)
        
        # Assert
        assert result is False
        
    def test_is_token_blacklisted_when_blacklisted(self, db_session: Session):
        """Test checking if a token is blacklisted when it is"""
        # Arrange
        jti = "test-jti"
        expires_at = datetime.utcnow() + timedelta(days=30)
        token = Token(jti=jti, is_blacklisted=True, expires_at=expires_at)
        db_session.add(token)
        db_session.commit()
        
        # Act
        result = is_token_blacklisted(session=db_session, jti=jti)
        
        # Assert
        assert result is True
    
    def test_blacklist_token(self, db_session: Session):
        """Test blacklisting a token"""
        # Create a real refresh token for a user
        user_id = 123
        refresh_token = create_refresh_token(user_id)
        
        # Act - Blacklist the token
        blacklist_token(session=db_session, token=refresh_token)
        
        # Decode the token manually to get the JTI
        from app.core.security import decode_token
        payload = decode_token(refresh_token)
        jti = payload.get("jti")
        
        # Assert
        token = get_token_by_jti(session=db_session, jti=jti)
        assert token is not None
        assert token.jti == jti
        assert token.is_blacklisted is True
    
    def test_blacklist_token_invalid_token(self, db_session: Session):
        """Test blacklisting an invalid token doesn't cause errors"""
        # Act - try to blacklist an invalid token
        blacklist_token(session=db_session, token="invalid_token")
        
        # No assertion needed, just verifying no exception is raised
    
    def test_blacklist_token_already_blacklisted(self, db_session: Session):
        """Test blacklisting an already blacklisted token"""
        # Create a real refresh token for a user
        user_id = 123
        refresh_token = create_refresh_token(user_id)
        
        # Blacklist the token
        blacklist_token(session=db_session, token=refresh_token)
        
        # Get the token count
        from app.core.security import decode_token
        payload = decode_token(refresh_token)
        jti = payload.get("jti")
        initial_count = db_session.query(Token).count()
        
        # Try to blacklist again
        blacklist_token(session=db_session, token=refresh_token)
        
        # Assert no new token was added
        new_count = db_session.query(Token).count()
        assert new_count == initial_count
    
    def test_manual_blacklist_entry(self, db_session: Session):
        """Test directly adding a blacklisted token to the database"""
        # Arrange
        jti = str(uuid.uuid4())
        exp = datetime.utcnow() + timedelta(days=30)
        
        # Create blacklisted entry directly
        token_entry = Token(
            jti=jti,
            is_blacklisted=True,
            expires_at=exp
        )
        db_session.add(token_entry)
        db_session.commit()
        
        # Act
        is_blacklisted = is_token_blacklisted(session=db_session, jti=jti)
        
        # Assert
        assert is_blacklisted is True
    
    def test_get_expired_tokens(self, db_session: Session):
        """Test retrieving expired tokens"""
        # Arrange
        # Create expired token
        expired_jti = "expired-jti"
        expired_at = datetime.utcnow() - timedelta(days=1)
        expired_token = Token(jti=expired_jti, is_blacklisted=False, expires_at=expired_at)
        db_session.add(expired_token)
        
        # Create non-expired token
        valid_jti = "valid-jti"
        valid_expires_at = datetime.utcnow() + timedelta(days=30)
        valid_token = Token(jti=valid_jti, is_blacklisted=False, expires_at=valid_expires_at)
        db_session.add(valid_token)
        
        db_session.commit()
        
        # Act
        expired_tokens = get_expired_tokens(session=db_session)
        
        # Assert
        assert len(expired_tokens) == 1
        assert expired_tokens[0].jti == expired_jti
        
    @patch('app.services.token.Session')
    @patch('app.services.token.get_expired_tokens')
    def test_purge_expired_tokens(self, mock_get_expired, mock_session):
        """Test purging expired tokens"""
        # Setup mocks
        mock_session_instance = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_session_instance
        
        # Create mock expired tokens
        expired_token1 = Token(jti="expired1", is_blacklisted=True, expires_at=datetime.utcnow() - timedelta(days=1))
        expired_token2 = Token(jti="expired2", is_blacklisted=True, expires_at=datetime.utcnow() - timedelta(days=2))
        mock_get_expired.return_value = [expired_token1, expired_token2]
        
        # Act
        purge_expired_tokens()
        
        # Assert
        mock_get_expired.assert_called_once_with(session=mock_session_instance)
        assert mock_session_instance.delete.call_count == 2
        mock_session_instance.commit.assert_called_once()
        
    @patch('app.services.token.Session')
    @patch('app.services.token.get_expired_tokens')
    def test_purge_expired_tokens_no_tokens(self, mock_get_expired, mock_session):
        """Test purging when there are no expired tokens"""
        # Setup mocks
        mock_session_instance = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_session_instance
        mock_get_expired.return_value = []
        
        # Act
        purge_expired_tokens()
        
        # Assert
        mock_get_expired.assert_called_once_with(session=mock_session_instance)
        mock_session_instance.delete.assert_not_called()
        mock_session_instance.commit.assert_not_called()
        
    @patch('app.services.token.Session')
    @patch('app.services.token.get_expired_tokens')
    @patch('app.services.token.logger')
    def test_purge_expired_tokens_exception(self, mock_logger, mock_get_expired, mock_session):
        """Test error handling in purge_expired_tokens"""
        # Setup mock to raise exception
        mock_session.return_value.__enter__.side_effect = Exception("Database error")
        
        # Act
        purge_expired_tokens()
        
        # Assert
        mock_logger.error.assert_called_once()
        # Verify error message contains the exception info
        args, _ = mock_logger.error.call_args
        assert "Database error" in args[0]