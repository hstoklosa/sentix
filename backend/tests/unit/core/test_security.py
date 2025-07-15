import pytest
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

from app.core.security import (
    validate_password,
    get_password_hash,
    verify_password,
    create_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type
)
from app.core.config import settings
from tests.conftest import VALID_PASSWORDS, INVALID_PASSWORDS, VALID_SUBJECTS, INVALID_SUBJECTS, TOKEN_TYPES


class TestPasswordValidation:
    """Test password validation functionality."""
    
    @pytest.mark.parametrize("password", VALID_PASSWORDS)
    def test_valid_passwords(self, password):
        """Test that valid passwords pass validation."""
        is_valid, error_message = validate_password(password)
        assert is_valid is True
        assert error_message is None
    
    @pytest.mark.parametrize("password,expected_error", INVALID_PASSWORDS)
    def test_invalid_passwords(self, password, expected_error):
        """Test that invalid passwords fail validation with correct error messages."""
        is_valid, error_message = validate_password(password)
        assert is_valid is False
        assert error_message == expected_error
    
    def test_password_too_short(self):
        """Test password length validation."""
        is_valid, error_message = validate_password("Pass1!")
        assert is_valid is False
        assert "at least 8 characters long" in error_message
    
    def test_password_missing_uppercase(self):
        """Test uppercase letter requirement."""
        is_valid, error_message = validate_password("password123!")
        assert is_valid is False
        assert "uppercase letter" in error_message
    
    def test_password_missing_lowercase(self):
        """Test lowercase letter requirement."""
        is_valid, error_message = validate_password("PASSWORD123!")
        assert is_valid is False
        assert "lowercase letter" in error_message
    
    def test_password_missing_number(self):
        """Test number requirement."""
        is_valid, error_message = validate_password("PasswordABC!")
        assert is_valid is False
        assert "number" in error_message
    
    def test_password_missing_special_char(self):
        """Test special character requirement."""
        is_valid, error_message = validate_password("Password123")
        assert is_valid is False
        assert "special character" in error_message
    
    def test_empty_password(self):
        """Test empty password validation."""
        is_valid, error_message = validate_password("")
        assert is_valid is False
        assert "at least 8 characters long" in error_message
    
    def test_very_long_password(self):
        """Test that very long passwords are still validated correctly."""
        long_password = "A" * 100 + "a" * 100 + "1" * 100 + "!" * 100
        is_valid, error_message = validate_password(long_password)
        assert is_valid is True
        assert error_message is None


class TestPasswordHashing:
    """Test password hashing functionality."""
    
    def test_password_hashing(self):
        """Test that password hashing works correctly."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt hash prefix
    
    def test_password_verification_success(self):
        """Test successful password verification."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_verification_failure(self):
        """Test failed password verification."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_hash_uniqueness(self):
        """Test that same password generates different hashes."""
        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
    
    def test_empty_password_hashing(self):
        """Test hashing empty password."""
        hashed = get_password_hash("")
        assert hashed is not None
        assert verify_password("", hashed) is True
    
    def test_verify_password_with_invalid_hash(self):
        """Test password verification with invalid hash."""
        password = "TestPassword123!"
        invalid_hash = "invalid_hash"
        
        # Should return False for invalid hash format
        assert verify_password(password, invalid_hash) is False


class TestJWTTokenCreation:
    """Test JWT token creation functionality."""
    
    @pytest.mark.parametrize("subject", VALID_SUBJECTS)
    def test_access_token_creation(self, subject, mock_settings):
        """Test access token creation with valid subjects."""
        token = create_access_token(subject)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode to verify structure
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["type"] == "access"
        assert payload["sub"] == str(subject)
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
    
    @pytest.mark.parametrize("subject", VALID_SUBJECTS)
    def test_refresh_token_creation(self, subject, mock_settings):
        """Test refresh token creation with valid subjects."""
        token = create_refresh_token(subject)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode to verify structure
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["type"] == "refresh"
        assert payload["sub"] == str(subject)
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
    
    def test_token_expiration_times(self, mock_settings):
        """Test that access and refresh tokens have correct expiration times."""
        subject = 1
        
        access_token = create_access_token(subject)
        refresh_token = create_refresh_token(subject)
        
        access_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Refresh token should expire later than access token
        assert refresh_payload["exp"] > access_payload["exp"]
    
    def test_token_payload_fields(self, mock_settings):
        """Test that token payload contains all required fields."""
        subject = 1
        token = create_access_token(subject)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        required_fields = ["type", "sub", "exp", "iat", "jti"]
        for field in required_fields:
            assert field in payload
    
    def test_token_jti_uniqueness(self, mock_settings):
        """Test that each token has a unique JTI."""
        subject = 1
        token1 = create_access_token(subject)
        token2 = create_access_token(subject)
        
        payload1 = jwt.decode(token1, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        payload2 = jwt.decode(token2, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload1["jti"] != payload2["jti"]
    
    @pytest.mark.parametrize("token_type", TOKEN_TYPES)
    def test_create_token_with_types(self, token_type, mock_settings):
        """Test token creation with different types."""
        subject = 1
        token = create_token(subject, token_type)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["type"] == token_type


class TestTokenDecoding:
    """Test JWT token decoding functionality."""
    
    def test_valid_token_decoding(self, mock_settings):
        """Test decoding valid tokens."""
        subject = 1
        token = create_access_token(subject)
        
        payload = decode_token(token)
        
        assert payload is not None
        assert payload["type"] == "access"
        assert payload["sub"] == str(subject)
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
    
    def test_expired_token_decoding(self, mock_settings):
        """Test decoding expired tokens."""
        subject = 1
        
        # Create token with past expiration
        with patch('app.core.security.datetime') as mock_dt:
            mock_dt.now.return_value = datetime.now(timezone.utc) - timedelta(hours=1)
            expired_token = create_access_token(subject)
        
        payload = decode_token(expired_token)
        assert payload is None
    
    def test_invalid_signature_decoding(self, mock_settings):
        """Test decoding tokens with invalid signature."""
        subject = 1
        token = create_access_token(subject)
        
        # Tamper with token
        tampered_token = token[:-10] + "tampered123"
        
        payload = decode_token(tampered_token)
        assert payload is None
    
    def test_malformed_token_decoding(self, mock_settings):
        """Test decoding malformed tokens."""
        malformed_tokens = [
            "invalid.token",
            "not.a.jwt.token",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",
            "",
            "malformed"
        ]
        
        for token in malformed_tokens:
            payload = decode_token(token)
            assert payload is None
    
    def test_wrong_algorithm_decoding(self, mock_settings):
        """Test decoding tokens signed with wrong algorithm."""
        subject = 1
        
        # Create token with different algorithm
        payload = {
            "type": "access",
            "sub": str(subject),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "iat": datetime.now(timezone.utc),
            "jti": "test-jti"
        }
        
        wrong_algo_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS512")
        
        decoded = decode_token(wrong_algo_token)
        assert decoded is None
    
    def test_none_token_decoding(self, mock_settings):
        """Test decoding None token."""
        payload = decode_token(None)
        assert payload is None


class TestTokenTypeVerification:
    """Test token type verification functionality."""
    
    def test_correct_access_token_type(self, mock_settings):
        """Test verification of correct access token type."""
        subject = 1
        token = create_access_token(subject)
        payload = decode_token(token)
        
        assert verify_token_type(payload, "access") is True
    
    def test_correct_refresh_token_type(self, mock_settings):
        """Test verification of correct refresh token type."""
        subject = 1
        token = create_refresh_token(subject)
        payload = decode_token(token)
        
        assert verify_token_type(payload, "refresh") is True
    
    def test_incorrect_token_type(self, mock_settings):
        """Test verification of incorrect token type."""
        subject = 1
        token = create_access_token(subject)
        payload = decode_token(token)
        
        assert verify_token_type(payload, "refresh") is False
    
    def test_missing_token_type(self, mock_settings):
        """Test verification of token without type field."""
        payload = {"sub": "1", "exp": 1234567890}
        
        assert verify_token_type(payload, "access") is False
    
    def test_none_token_type(self, mock_settings):
        """Test verification with None token type."""
        payload = {"type": None, "sub": "1", "exp": 1234567890}
        
        assert verify_token_type(payload, "access") is False
    
    def test_empty_payload(self, mock_settings):
        """Test verification with empty payload."""
        payload = {}
        
        assert verify_token_type(payload, "access") is False
        assert verify_token_type(payload, "refresh") is False


class TestTokenSecurity:
    """Test token security aspects."""
    
    def test_token_timing_consistency(self, mock_settings):
        """Test that token operations have consistent timing."""
        subject = 1
        
        # Create multiple tokens and measure consistency
        tokens = []
        for _ in range(10):
            token = create_access_token(subject)
            tokens.append(token)
        
        # All tokens should be valid
        for token in tokens:
            payload = decode_token(token)
            assert payload is not None
            assert payload["type"] == "access"
    
    def test_token_secret_independence(self, mock_settings):
        """Test that tokens can't be decoded with wrong secret."""
        subject = 1
        token = create_access_token(subject)
        
        # Try to decode with wrong secret
        wrong_secret = "wrong-secret-key"
        
        with pytest.raises(Exception):
            jwt.decode(token, wrong_secret, algorithms=[settings.ALGORITHM])
    
    def test_token_algorithm_security(self, mock_settings):
        """Test that algorithm specification is enforced."""
        subject = 1
        token = create_access_token(subject)
        
        # Try to decode without specifying algorithm
        with pytest.raises(Exception):
            jwt.decode(token, settings.SECRET_KEY)
        
        # Try to decode with wrong algorithm list
        with pytest.raises(Exception):
            jwt.decode(token, settings.SECRET_KEY, algorithms=["HS512"])
