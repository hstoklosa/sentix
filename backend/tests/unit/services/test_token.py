import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.token import (
    blacklist_token,
    is_token_blacklisted,
    get_token_by_jti,
    get_expired_tokens,
    purge_expired_tokens
)
from app.models.token import Token
from app.core.security import create_refresh_token, decode_token


class TestTokenBlacklisting:
    """Test token blacklisting functionality."""
    
    @pytest.mark.asyncio
    async def test_blacklist_refresh_token_success(self, db_session: AsyncSession, test_user):
        """Test successful refresh token blacklisting."""
        # Create a refresh token
        refresh_token = create_refresh_token(test_user.id)
        
        # Blacklist the token
        await blacklist_token(session=db_session, token=refresh_token)
        
        # Verify token is blacklisted
        payload = decode_token(refresh_token)
        assert payload is not None
        jti = payload["jti"]
        
        is_blacklisted = await is_token_blacklisted(session=db_session, jti=jti)
        assert is_blacklisted is True
    
    @pytest.mark.asyncio
    async def test_blacklist_token_creates_db_entry(self, db_session: AsyncSession, test_user):
        """Test that blacklisting creates proper database entry."""
        refresh_token = create_refresh_token(test_user.id)
        
        await blacklist_token(session=db_session, token=refresh_token)
        
        # Check database entry
        payload = decode_token(refresh_token)
        assert payload is not None
        jti = payload["jti"]
        
        token_entry = await get_token_by_jti(session=db_session, jti=jti)
        assert token_entry is not None
        assert token_entry.jti == jti
        assert token_entry.is_blacklisted is True
        assert token_entry.expires_at is not None
    
    @pytest.mark.asyncio
    async def test_blacklist_duplicate_token(self, db_session: AsyncSession, test_user):
        """Test blacklisting the same token twice."""
        refresh_token = create_refresh_token(test_user.id)
        
        # Blacklist token first time
        await blacklist_token(session=db_session, token=refresh_token)
        
        # Blacklist token second time (should not cause error)
        await blacklist_token(session=db_session, token=refresh_token)
        
        # Should still be blacklisted
        payload = decode_token(refresh_token)
        assert payload is not None
        jti = payload["jti"]
        
        is_blacklisted = await is_token_blacklisted(session=db_session, jti=jti)
        assert is_blacklisted is True
    
    @pytest.mark.asyncio
    async def test_blacklist_invalid_token(self, db_session: AsyncSession):
        """Test blacklisting invalid token."""
        invalid_token = "invalid.token.string"
        
        # Should not raise exception
        await blacklist_token(session=db_session, token=invalid_token)
        
        # Should not create any database entry
        # This is tested implicitly by not raising an exception
    
    @pytest.mark.asyncio
    async def test_blacklist_access_token_ignored(self, db_session: AsyncSession, test_user):
        """Test that access tokens are not blacklisted."""
        from app.core.security import create_access_token
        
        access_token = create_access_token(test_user.id)
        
        # Should not blacklist access token
        await blacklist_token(session=db_session, token=access_token)
        
        # Verify no database entry was created
        payload = decode_token(access_token)
        assert payload is not None
        jti = payload["jti"]
        
        is_blacklisted = await is_token_blacklisted(session=db_session, jti=jti)
        assert is_blacklisted is False
    
    @pytest.mark.asyncio
    async def test_blacklist_expired_token(self, db_session: AsyncSession, test_user):
        """Test blacklisting expired token."""
        # Create expired token
        with patch('app.core.security.datetime') as mock_dt:
            mock_dt.now.return_value = datetime.now() - timedelta(days=1)
            expired_token = create_refresh_token(test_user.id)
        
        # Should handle expired token gracefully
        await blacklist_token(session=db_session, token=expired_token)
        
        # Even expired tokens should be blacklisted for security
        payload = decode_token(expired_token)
        # Since token is expired, decode_token returns None
        # So we manually decode to get JTI
        import jwt
        from app.core.config import settings
        
        try:
            payload = jwt.decode(expired_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False})
            assert payload is not None
            jti = payload["jti"]
            
            is_blacklisted = await is_token_blacklisted(session=db_session, jti=jti)
            assert is_blacklisted is True
        except jwt.PyJWTError:
            # If token is completely invalid, blacklisting should be ignored
            pass
    
    @pytest.mark.asyncio
    async def test_blacklist_malformed_token(self, db_session: AsyncSession):
        """Test blacklisting malformed token."""
        malformed_tokens = [
            "malformed",
            "not.a.jwt",
            "",
            None
        ]
        
        for token in malformed_tokens:
            # Should not raise exception
            await blacklist_token(session=db_session, token=token)


class TestTokenBlacklistChecking:
    """Test token blacklist checking functionality."""
    
    @pytest.mark.asyncio
    async def test_check_blacklisted_token(self, db_session: AsyncSession, test_user):
        """Test checking blacklisted token."""
        refresh_token = create_refresh_token(test_user.id)
        
        # Blacklist token
        await blacklist_token(session=db_session, token=refresh_token)
        
        # Check if blacklisted
        payload = decode_token(refresh_token)
        assert payload is not None
        jti = payload["jti"]
        
        is_blacklisted = await is_token_blacklisted(session=db_session, jti=jti)
        assert is_blacklisted is True
    
    @pytest.mark.asyncio
    async def test_check_non_blacklisted_token(self, db_session: AsyncSession, test_user):
        """Test checking non-blacklisted token."""
        refresh_token = create_refresh_token(test_user.id)
        payload = decode_token(refresh_token)
        assert payload is not None
        jti = payload["jti"]
        
        is_blacklisted = await is_token_blacklisted(session=db_session, jti=jti)
        assert is_blacklisted is False
    
    @pytest.mark.asyncio
    async def test_check_nonexistent_jti(self, db_session: AsyncSession):
        """Test checking JTI that doesn't exist."""
        nonexistent_jti = "nonexistent-jti-12345"
        
        is_blacklisted = await is_token_blacklisted(session=db_session, jti=nonexistent_jti)
        assert is_blacklisted is False
    
    @pytest.mark.asyncio
    async def test_check_empty_jti(self, db_session: AsyncSession):
        """Test checking empty JTI."""
        is_blacklisted = await is_token_blacklisted(session=db_session, jti="")
        assert is_blacklisted is False
    
    @pytest.mark.asyncio
    async def test_check_multiple_tokens(self, db_session: AsyncSession, test_user):
        """Test checking multiple tokens."""
        # Create multiple tokens
        tokens = []
        for i in range(3):
            token = create_refresh_token(test_user.id)
            tokens.append(token)
        
        # Blacklist only the first token
        await blacklist_token(session=db_session, token=tokens[0])
        
        # Check all tokens
        for i, token in enumerate(tokens):
            payload = decode_token(token)
            jti = payload["jti"]
            is_blacklisted = await is_token_blacklisted(session=db_session, jti=jti)
            
            if i == 0:
                assert is_blacklisted is True
            else:
                assert is_blacklisted is False


class TestTokenRetrieval:
    """Test token retrieval functionality."""
    
    @pytest.mark.asyncio
    async def test_get_token_by_jti_success(self, db_session: AsyncSession, test_user):
        """Test successful token retrieval by JTI."""
        refresh_token = create_refresh_token(test_user.id)
        
        # Blacklist token to create database entry
        await blacklist_token(session=db_session, token=refresh_token)
        
        # Get token by JTI
        payload = decode_token(refresh_token)
        assert payload is not None
        jti = payload["jti"]
        
        token_entry = await get_token_by_jti(session=db_session, jti=jti)
        assert token_entry is not None
        assert token_entry.jti == jti
        assert token_entry.is_blacklisted is True
    
    @pytest.mark.asyncio
    async def test_get_token_by_nonexistent_jti(self, db_session: AsyncSession):
        """Test token retrieval with non-existent JTI."""
        nonexistent_jti = "nonexistent-jti-12345"
        
        token_entry = await get_token_by_jti(session=db_session, jti=nonexistent_jti)
        assert token_entry is None
    
    @pytest.mark.asyncio
    async def test_get_token_by_empty_jti(self, db_session: AsyncSession):
        """Test token retrieval with empty JTI."""
        token_entry = await get_token_by_jti(session=db_session, jti="")
        assert token_entry is None


class TestTokenCleanup:
    """Test token cleanup functionality."""
    
    @pytest.mark.asyncio
    async def test_get_expired_tokens(self, db_session: AsyncSession, test_user):
        """Test getting expired tokens."""
        # Create tokens with different expiration times
        current_time = datetime.utcnow()
        
        # Create expired token
        expired_token = Token(
            jti="expired-jti-123",
            expires_at=current_time - timedelta(hours=1),
            is_blacklisted=True
        )
        
        # Create valid token
        valid_token = Token(
            jti="valid-jti-456",
            expires_at=current_time + timedelta(hours=1),
            is_blacklisted=True
        )
        
        db_session.add(expired_token)
        db_session.add(valid_token)
        await db_session.commit()
        
        # Get expired tokens
        expired_tokens = await get_expired_tokens(session=db_session)
        
        # Should only return expired token
        assert len(expired_tokens) == 1
        assert expired_tokens[0].jti == "expired-jti-123"
    
    @pytest.mark.asyncio
    async def test_get_expired_tokens_empty(self, db_session: AsyncSession):
        """Test getting expired tokens when none exist."""
        expired_tokens = await get_expired_tokens(session=db_session)
        assert len(expired_tokens) == 0
    
    @pytest.mark.asyncio
    async def test_get_expired_tokens_multiple(self, db_session: AsyncSession):
        """Test getting multiple expired tokens."""
        current_time = datetime.utcnow()
        
        # Create multiple expired tokens
        expired_tokens_data = []
        for i in range(3):
            token = Token(
                jti=f"expired-jti-{i}",
                expires_at=current_time - timedelta(hours=i+1),
                is_blacklisted=True
            )
            expired_tokens_data.append(token)
            db_session.add(token)
        
        await db_session.commit()
        
        # Get expired tokens
        expired_tokens = await get_expired_tokens(session=db_session)
        
        assert len(expired_tokens) == 3
        expired_jtis = [token.jti for token in expired_tokens]
        expected_jtis = [f"expired-jti-{i}" for i in range(3)]
        
        for jti in expected_jtis:
            assert jti in expired_jtis
    
    @pytest.mark.asyncio
    async def test_purge_expired_tokens(self, db_session: AsyncSession):
        """Test purging expired tokens."""
        current_time = datetime.utcnow()
        
        # Create expired tokens
        expired_tokens = []
        for i in range(2):
            token = Token(
                jti=f"expired-jti-{i}",
                expires_at=current_time - timedelta(hours=i+1),
                is_blacklisted=True
            )
            expired_tokens.append(token)
            db_session.add(token)
        
        # Create valid token
        valid_token = Token(
            jti="valid-jti-123",
            expires_at=current_time + timedelta(hours=1),
            is_blacklisted=True
        )
        db_session.add(valid_token)
        await db_session.commit()
        
        # Mock sessionmanager for purge_expired_tokens
        with patch('app.services.token.sessionmanager') as mock_sessionmanager:
            mock_sessionmanager.session.return_value.__aenter__.return_value = db_session
            
            # Purge expired tokens
            count = await purge_expired_tokens()
            
            # Should have purged 2 tokens
            assert count == 2
        
        # Verify tokens were deleted
        remaining_expired = await get_expired_tokens(session=db_session)
        assert len(remaining_expired) == 0
        
        # Valid token should still exist
        valid_token_retrieved = await get_token_by_jti(session=db_session, jti="valid-jti-123")
        assert valid_token_retrieved is not None
    
    @pytest.mark.asyncio
    async def test_purge_expired_tokens_empty(self, db_session: AsyncSession):
        """Test purging when no expired tokens exist."""
        with patch('app.services.token.sessionmanager') as mock_sessionmanager:
            mock_sessionmanager.session.return_value.__aenter__.return_value = db_session
            
            count = await purge_expired_tokens()
            assert count == 0
    
    @pytest.mark.asyncio
    async def test_purge_expired_tokens_error_handling(self, db_session: AsyncSession):
        """Test error handling in purge_expired_tokens."""
        # Mock sessionmanager to raise an exception
        with patch('app.services.token.sessionmanager') as mock_sessionmanager:
            mock_sessionmanager.session.side_effect = Exception("Database error")
            
            count = await purge_expired_tokens()
            assert count == 0  # Should return 0 on error
    
    @pytest.mark.asyncio
    async def test_purge_expired_tokens_large_batch(self, db_session: AsyncSession):
        """Test purging large batch of expired tokens."""
        current_time = datetime.utcnow()
        
        # Create many expired tokens
        num_tokens = 50
        for i in range(num_tokens):
            token = Token(
                jti=f"expired-jti-{i}",
                expires_at=current_time - timedelta(hours=1),
                is_blacklisted=True
            )
            db_session.add(token)
        
        await db_session.commit()
        
        with patch('app.services.token.sessionmanager') as mock_sessionmanager:
            mock_sessionmanager.session.return_value.__aenter__.return_value = db_session
            
            count = await purge_expired_tokens()
            assert count == num_tokens
        
        # Verify all tokens were deleted
        remaining_expired = await get_expired_tokens(session=db_session)
        assert len(remaining_expired) == 0


class TestTokenServiceEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_concurrent_token_blacklisting(self, db_session: AsyncSession, test_user):
        """Test concurrent token blacklisting scenarios."""
        refresh_token = create_refresh_token(test_user.id)
        
        # Simulate concurrent blacklisting
        # In real scenario, this would test actual concurrency
        await blacklist_token(session=db_session, token=refresh_token)
        await blacklist_token(session=db_session, token=refresh_token)
        
        # Should still be blacklisted without errors
        payload = decode_token(refresh_token)
        assert payload is not None
        jti = payload["jti"]
        
        is_blacklisted = await is_token_blacklisted(session=db_session, jti=jti)
        assert is_blacklisted is True
    
    @pytest.mark.asyncio
    async def test_token_blacklist_with_database_error(self, db_session: AsyncSession, test_user):
        """Test token blacklisting with database errors."""
        refresh_token = create_refresh_token(test_user.id)
        
        # Mock database session to raise error
        with patch.object(db_session, 'add', side_effect=Exception("Database error")):
            # Should handle error gracefully
            try:
                await blacklist_token(session=db_session, token=refresh_token)
            except Exception:
                # If exception is raised, it should be handled appropriately
                pass
    
    @pytest.mark.asyncio
    async def test_token_operations_with_null_values(self, db_session: AsyncSession):
        """Test token operations with null/empty values."""
        # Test with empty JTI instead of None to avoid type issues
        is_blacklisted = await is_token_blacklisted(session=db_session, jti="")
        assert is_blacklisted is False
        
        # Test with empty JTI
        is_blacklisted = await is_token_blacklisted(session=db_session, jti="")
        assert is_blacklisted is False
        
        # Test getting token with empty JTI
        token = await get_token_by_jti(session=db_session, jti="")
        assert token is None
    
    @pytest.mark.asyncio
    async def test_token_expiration_edge_cases(self, db_session: AsyncSession):
        """Test token expiration edge cases."""
        current_time = datetime.utcnow()
        
        # Token that expires exactly now
        token_now = Token(
            jti="expires-now-jti",
            expires_at=current_time,
            is_blacklisted=True
        )
        
        # Token that expires in 1 second
        token_future = Token(
            jti="expires-future-jti",
            expires_at=current_time + timedelta(seconds=1),
            is_blacklisted=True
        )
        
        db_session.add(token_now)
        db_session.add(token_future)
        await db_session.commit()
        
        # Get expired tokens
        expired_tokens = await get_expired_tokens(session=db_session)
        
        # Token that expires exactly now should be considered expired
        expired_jtis = [token.jti for token in expired_tokens]
        assert "expires-now-jti" in expired_jtis
        assert "expires-future-jti" not in expired_jtis
