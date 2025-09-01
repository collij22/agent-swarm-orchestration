"""
Unit tests for core modules (config, security).
"""
import pytest
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

from app.core.config import Settings, get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_password_hash,
    verify_password
)


class TestSettings:
    """Test configuration settings."""
    
    def test_settings_creation(self):
        """Test that settings can be created with defaults."""
        settings = Settings()
        assert settings.PROJECT_NAME == "QuickShop MVP"
        assert settings.VERSION == "1.0.0"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7
    
    def test_database_url_construction(self):
        """Test database URL construction."""
        settings = Settings(
            DB_HOST="localhost",
            DB_PORT=5432,
            DB_NAME="quickshop",
            DB_USER="user",
            DB_PASSWORD="pass"
        )
        expected_url = "postgresql://user:pass@localhost:5432/quickshop"
        assert settings.DATABASE_URL == expected_url
    
    def test_redis_url_construction(self):
        """Test Redis URL construction."""
        settings = Settings(
            REDIS_HOST="localhost",
            REDIS_PORT=6379,
            REDIS_PASSWORD="redispass"
        )
        expected_url = "redis://:redispass@localhost:6379"
        assert settings.REDIS_URL == expected_url
    
    def test_get_settings_singleton(self):
        """Test that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


class TestSecurity:
    """Test security functions."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "test@example.com"}
        token = create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_token_with_expiration(self):
        """Test token creation with custom expiration."""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=15)
        token = create_access_token(data, expires_delta=expires_delta)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    @patch('app.core.security.jwt.decode')
    def test_verify_token_valid(self, mock_decode):
        """Test token verification with valid token."""
        mock_decode.return_value = {"sub": "test@example.com", "exp": datetime.utcnow().timestamp() + 3600}
        
        payload = verify_token("valid_token")
        assert payload is not None
        assert payload["sub"] == "test@example.com"
    
    @patch('app.core.security.jwt.decode')
    def test_verify_token_invalid(self, mock_decode):
        """Test token verification with invalid token."""
        mock_decode.side_effect = Exception("Invalid token")
        
        payload = verify_token("invalid_token")
        assert payload is None
    
    def test_token_roundtrip(self):
        """Test creating and verifying a token."""
        data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(data)
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "test@example.com"
        assert payload["user_id"] == 1


class TestSecurityEdgeCases:
    """Test security edge cases and error conditions."""
    
    def test_empty_password_hash(self):
        """Test hashing empty password."""
        with pytest.raises(ValueError):
            get_password_hash("")
    
    def test_none_password_hash(self):
        """Test hashing None password."""
        with pytest.raises((ValueError, TypeError)):
            get_password_hash(None)
    
    def test_verify_password_with_none(self):
        """Test password verification with None values."""
        hashed = get_password_hash("testpassword")
        
        assert verify_password(None, hashed) is False
        assert verify_password("testpassword", None) is False
        assert verify_password(None, None) is False
    
    def test_token_with_empty_data(self):
        """Test token creation with empty data."""
        token = create_access_token({})
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_empty_token(self):
        """Test verification of empty token."""
        payload = verify_token("")
        assert payload is None
    
    def test_verify_none_token(self):
        """Test verification of None token."""
        payload = verify_token(None)
        assert payload is None


@pytest.mark.security
class TestSecurityCompliance:
    """Test security compliance requirements."""
    
    def test_password_hash_strength(self):
        """Test that password hashes are sufficiently strong."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # Hash should be at least 60 characters (bcrypt standard)
        assert len(hashed) >= 60
        # Should start with $2b$ (bcrypt identifier)
        assert hashed.startswith("$2b$")
    
    def test_token_contains_no_sensitive_data(self):
        """Test that tokens don't contain sensitive information."""
        import base64
        import json
        
        data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(data)
        
        # Decode JWT payload (without verification for testing)
        parts = token.split('.')
        payload_encoded = parts[1]
        # Add padding if needed
        payload_encoded += '=' * (4 - len(payload_encoded) % 4)
        payload_decoded = base64.b64decode(payload_encoded)
        payload_json = json.loads(payload_decoded)
        
        # Should not contain password or other sensitive data
        assert "password" not in payload_json
        assert "secret" not in payload_json
        assert "key" not in payload_json
    
    def test_token_expiration_reasonable(self):
        """Test that token expiration times are reasonable."""
        import base64
        import json
        
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        # Decode JWT payload
        parts = token.split('.')
        payload_encoded = parts[1]
        payload_encoded += '=' * (4 - len(payload_encoded) % 4)
        payload_decoded = base64.b64decode(payload_encoded)
        payload_json = json.loads(payload_decoded)
        
        # Token should expire within reasonable time (default 30 minutes)
        exp_time = datetime.fromtimestamp(payload_json['exp'])
        current_time = datetime.utcnow()
        time_diff = exp_time - current_time
        
        assert time_diff <= timedelta(minutes=35)  # Allow some buffer
        assert time_diff >= timedelta(minutes=25)  # Should be at least 25 minutes