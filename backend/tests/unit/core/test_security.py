import pytest
import jwt
from datetime import datetime, timedelta
from freezegun import freeze_time

from app.core.security import (
    validate_password,
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type
)
from app.core.config import settings


class TestPasswordSecurity:
    """Unit tests for password security functions"""
    
    def test_password_validation_valid(self):
        """Test that valid passwords pass validation"""
        valid_passwords = [
            "Password123!",
            "StrongP@ss123",
            "C0mpl3x!P@ssw0rd",
            "Aa1!aaaaaaaaaa"
        ]
        
        for password in valid_passwords:
            is_valid, error = validate_password(password)
            assert is_valid is True
            assert error is None
    
    def test_password_validation_too_short(self):
        """Test validation rejects passwords that are too short"""
        password = "Pass1!"
        is_valid, error = validate_password(password)
        
        assert is_valid is False
        assert "at least 8 characters" in error
    
    def test_password_validation_no_uppercase(self):
        """Test validation rejects passwords without uppercase letters"""
        password = "password123!"
        is_valid, error = validate_password(password)
        
        assert is_valid is False
        assert "uppercase letter" in error
    
    def test_password_validation_no_lowercase(self):
        """Test validation rejects passwords without lowercase letters"""
        password = "PASSWORD123!"
        is_valid, error = validate_password(password)
        
        assert is_valid is False
        assert "lowercase letter" in error
    
    def test_password_validation_no_digit(self):
        """Test validation rejects passwords without digits"""
        password = "Password!"
        is_valid, error = validate_password(password)
        
        assert is_valid is False
        assert "number" in error
    
    def test_password_validation_no_special_char(self):
        """Test validation rejects passwords without special characters"""
        password = "Password123"
        is_valid, error = validate_password(password)
        
        assert is_valid is False
        assert "special character" in error
    
    def test_password_hashing(self):
        """Test that password hashing works correctly"""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        
        # Hashed password should not be the same as original
        assert hashed != password
        
        # Hashed password should be a string with significant length (bcrypt hashes are longer)
        assert isinstance(hashed, str)
        assert len(hashed) > 20
    
    def test_password_verification(self):
        """Test that password verification works correctly"""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        
        # Correct password should verify
        assert verify_password(password, hashed) is True
        
        # Incorrect password should fail verification
        assert verify_password("WrongPassword123!", hashed) is False


class TestTokenSecurity:
    """Unit tests for JWT token security functions"""
    
    def test_create_access_token(self):
        """Test creating an access token"""
        # Create token with user ID
        user_id = 123
        token = create_access_token(user_id)
        
        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify contents
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"
        assert "jti" in payload  # Token ID for blacklisting
        assert "exp" in payload  # Expiration
    
    def test_create_refresh_token(self):
        """Test creating a refresh token"""
        # Create token with user ID
        user_id = 123
        token = create_refresh_token(user_id)
        
        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify contents
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"
        assert "jti" in payload
        assert "exp" in payload
    
    def test_token_expiration(self):
        """Test that tokens properly expire"""
        with freeze_time("2023-01-01 12:00:00"):
            # Create token at frozen time
            user_id = 123
            token = create_access_token(user_id)
            
            # Token should be valid initially
            payload = decode_token(token)
            assert payload is not None
            
            # Move time forward to just before expiration
            move_forward = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES - 1)
        
        # Test token is still valid just before expiration
        with freeze_time(datetime(2023, 1, 1, 12, 0, 0) + move_forward):
            payload = decode_token(token)
            assert payload is not None
            
            # Move time forward past expiration
            move_forward = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES + 1)
        
        # Test token is invalid after expiration
        with freeze_time(datetime(2023, 1, 1, 12, 0, 0) + move_forward):
            payload = decode_token(token)
            assert payload is None
    
    def test_token_type_verification(self):
        """Test that token type verification works correctly"""
        # Create tokens
        access_token = create_access_token(123)
        refresh_token = create_refresh_token(123)
        
        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)
        
        # Verify token types
        assert verify_token_type(access_payload, "access") is True
        assert verify_token_type(access_payload, "refresh") is False
        assert verify_token_type(refresh_payload, "refresh") is True
        assert verify_token_type(refresh_payload, "access") is False
    
    def test_invalid_token_decode(self):
        """Test decoding invalid tokens"""
        # Test with malformed token
        payload = decode_token("not.a.token")
        assert payload is None
        
        # Test with token signed with wrong key
        invalid_token = jwt.encode(
            {"sub": "123", "exp": datetime.utcnow() + timedelta(days=1)},
            "wrong_secret_key",
            algorithm=settings.ALGORITHM
        )
        payload = decode_token(invalid_token)
        assert payload is None