import pytest
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

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
from app.core.exceptions import InvalidTokenException


@pytest.mark.unit
class TestPasswordValidation:
    """Test password validation functionality."""
    
    def test_validate_password_valid(self):
        """Test password validation with a valid password."""
        valid_password = "TestPass123!"
        is_valid, error_message = validate_password(valid_password)
        
        assert is_valid is True
        assert error_message is None
    
    def test_validate_password_too_short(self):
        """Test password validation with a password that's too short."""
        short_password = "Test1!"
        is_valid, error_message = validate_password(short_password)
        
        assert is_valid is False
        assert "at least 8 characters" in error_message.lower()
    
    def test_validate_password_missing_uppercase(self):
        """Test password validation with missing uppercase letter."""
        password = "testpass123!"
        is_valid, error_message = validate_password(password)
        
        assert is_valid is False
        assert "uppercase" in error_message.lower()
    
    def test_validate_password_missing_lowercase(self):
        """Test password validation with missing lowercase letter."""
        password = "TESTPASS123!"
        is_valid, error_message = validate_password(password)
        
        assert is_valid is False
        assert "lowercase" in error_message.lower()
    
    def test_validate_password_missing_number(self):
        """Test password validation with missing number."""
        password = "TestPassword!"
        is_valid, error_message = validate_password(password)
        
        assert is_valid is False
        assert "number" in error_message.lower()
    
    def test_validate_password_missing_special_char(self):
        """Test password validation with missing special character."""
        password = "TestPassword123"
        is_valid, error_message = validate_password(password)
        
        assert is_valid is False
        assert "special character" in error_message.lower()
    
    @pytest.mark.parametrize("valid_password", [
        "Password123!",
        "MySecure@Pass1",
        "Complex#Password99",
        "Strong$Pass42",
        "Test&Password1"
    ])
    def test_validate_password_various_valid_passwords(self, valid_password):
        """Test password validation with various valid passwords."""
        is_valid, error_message = validate_password(valid_password)
        
        assert is_valid is True
        assert error_message is None


@pytest.mark.unit
class TestPasswordHashing:
    """Test password hashing functionality."""
    
    def test_get_password_hash_returns_string(self):
        """Test that password hashing returns a string hash."""
        password = "TestPass123!"
        hashed = get_password_hash(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password  # Should be different from original
        assert hashed.startswith("$2b$")  # bcrypt hash prefix
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPass123!"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "TestPass123!"
        wrong_password = "WrongPass456!"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_hash_uniqueness(self):
        """Test that the same password generates different hashes each time."""
        password = "TestPass123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
    
    def test_verify_password_with_invalid_hash(self):
        """Test password verification with invalid hash format."""
        password = "TestPass123!"
        invalid_hash = "invalid_hash_format"
        
        assert verify_password(password, invalid_hash) is False


@pytest.mark.unit
class TestTokenLogic:
    """Test JWT token creation and validation."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        subject = "123"
        token = create_access_token(subject=subject)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify claims
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == subject
        assert payload["type"] == "access"
        assert "jti" in payload
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        subject = "123"
        token = create_refresh_token(subject=subject)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify claims
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == subject
        assert payload["type"] == "refresh"
        assert "jti" in payload
        assert "exp" in payload
        assert "iat" in payload
    
    def test_decode_token_valid(self):
        """Test token decoding with valid token."""
        subject = "123"
        token = create_access_token(subject=subject)
        
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == subject
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
    
    def test_decode_token_expired(self):
        """Test token decoding with expired token."""
        subject = "123"
        
        # Create token that's already expired
        with patch('app.core.security.datetime') as mock_datetime:
            # Mock datetime to create token in the past
            past_time = datetime.now(timezone.utc) - timedelta(hours=1)
            mock_datetime.now.return_value = past_time
            token = create_access_token(subject=subject)
            
        # Try to decode expired token
        payload = decode_token(token)
        assert payload is None
    
    def test_decode_token_invalid(self):
        """Test token decoding with invalid token string."""
        invalid_tokens = [
            "invalid.token.string",
            "not.a.jwt.token.at.all",
            "",
            "malformed_token",
            None
        ]
        
        for invalid_token in invalid_tokens:
            if invalid_token is not None:
                payload = decode_token(invalid_token)
                assert payload is None
    
    def test_decode_token_tampered(self):
        """Test token decoding with tampered token."""
        subject = "123"
        token = create_access_token(subject=subject)
        
        # Tamper with the token
        tampered_token = token[:-10] + "tampered123"
        
        payload = decode_token(tampered_token)
        assert payload is None
    
    def test_verify_token_type_access(self):
        """Test token type verification for access token."""
        subject = "123"
        token = create_access_token(subject=subject)
        payload = decode_token(token)
        
        assert payload is not None
        assert verify_token_type(payload, "access") is True
        assert verify_token_type(payload, "refresh") is False
    
    def test_verify_token_type_refresh(self):
        """Test token type verification for refresh token."""
        subject = "123"
        token = create_refresh_token(subject=subject)
        payload = decode_token(token)
        
        assert payload is not None
        assert verify_token_type(payload, "refresh") is True
        assert verify_token_type(payload, "access") is False
    
    def test_verify_token_type_wrong_type(self):
        """Test token type verification with wrong type."""
        subject = "123"
        token = create_access_token(subject=subject)
        payload = decode_token(token)
        
        assert payload is not None
        # Should return False when expecting refresh but got access
        assert verify_token_type(payload, "refresh") is False
    
    def test_verify_token_type_missing_type(self):
        """Test token type verification with missing type field."""
        payload = {"sub": "123", "exp": 1234567890, "jti": "test-jti"}
        
        assert verify_token_type(payload, "access") is False
        assert verify_token_type(payload, "refresh") is False
    
    def test_verify_token_type_invalid_payload(self):
        """Test token type verification with invalid payload."""
        invalid_payloads = [
            {},
            {"type": None},
            {"type": ""},
            None
        ]
        
        for payload in invalid_payloads:
            if payload is not None:
                assert verify_token_type(payload, "access") is False
                assert verify_token_type(payload, "refresh") is False
    
    def test_token_expiration_times(self):
        """Test that access and refresh tokens have different expiration times."""
        subject = "123"
        
        access_token = create_access_token(subject)
        refresh_token = create_refresh_token(subject)
        
        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)
        
        assert access_payload is not None
        assert refresh_payload is not None
        
        # Refresh token should expire later than access token
        assert refresh_payload["exp"] > access_payload["exp"]
    
    def test_token_jti_uniqueness(self):
        """Test that each token has a unique JTI (JWT ID)."""
        subject = "123"
        
        token1 = create_access_token(subject)
        token2 = create_access_token(subject)
        
        payload1 = decode_token(token1)
        payload2 = decode_token(token2)
        
        assert payload1 is not None
        assert payload2 is not None
        assert payload1["jti"] != payload2["jti"]
    
    @pytest.mark.parametrize("subject", [
        "123",
        123,
        "user_456",
        999
    ])
    def test_token_creation_with_different_subjects(self, subject):
        """Test token creation with different subject types."""
        token = create_access_token(subject=subject)
        payload = decode_token(token)
        
        assert payload is not None
        assert payload["sub"] == str(subject)  # Subject should be converted to string
        assert payload["type"] == "access"
    
    def test_token_security_secret_key(self):
        """Test that tokens cannot be decoded with wrong secret key."""
        subject = "123"
        token = create_access_token(subject)
        
        # Try to decode with wrong secret
        wrong_secret = "wrong-secret-key"
        
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, wrong_secret, algorithms=[settings.ALGORITHM])
    
    def test_token_algorithm_security(self):
        """Test that algorithm specification is enforced."""
        subject = "123"
        token = create_access_token(subject)
        
        # Try to decode without specifying algorithm
        with pytest.raises(jwt.InvalidTokenError):
            jwt.decode(token, settings.SECRET_KEY)
        
        # Try to decode with wrong algorithm - should raise InvalidAlgorithmError
        with pytest.raises(jwt.InvalidAlgorithmError):
            jwt.decode(token, settings.SECRET_KEY, algorithms=["HS512"])
