"""
Security tests for DevPortfolio application.
Tests authentication, authorization, input validation, and security headers.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import jwt
import hashlib
import hmac
import json
from datetime import datetime, timedelta

from main import app
from utils.webhook_validator import WebhookValidator
from utils.advanced_webhook_validator import AdvancedWebhookValidator


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def webhook_validator():
    """Create webhook validator instance."""
    return WebhookValidator("test-secret")


@pytest.fixture
def advanced_webhook_validator():
    """Create advanced webhook validator instance."""
    return AdvancedWebhookValidator("test-secret")


@pytest.mark.security
class TestAuthenticationSecurity:
    """Test authentication security measures."""
    
    def test_jwt_token_validation(self, client):
        """Test JWT token validation."""
        # Test with invalid token
        response = client.get("/auth/me", headers={
            "Authorization": "Bearer invalid.token.here"
        })
        assert response.status_code == 401
        
        # Test with expired token
        expired_payload = {
            "sub": "test-user",
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_payload, "secret", algorithm="HS256")
        
        response = client.get("/auth/me", headers={
            "Authorization": f"Bearer {expired_token}"
        })
        assert response.status_code == 401

    def test_password_security_requirements(self, client):
        """Test password security requirements."""
        weak_passwords = [
            "123456",
            "password",
            "abc123",
            "qwerty",
            "12345678"
        ]
        
        for weak_password in weak_passwords:
            response = client.post("/auth/register", json={
                "username": "testuser",
                "email": "test@example.com",
                "password": weak_password
            })
            # Should reject weak passwords
            assert response.status_code in [400, 422]

    def test_brute_force_protection(self, client):
        """Test brute force attack protection."""
        # Simulate multiple failed login attempts
        for i in range(10):
            response = client.post("/auth/login", data={
                "username": "testuser",
                "password": f"wrong-password-{i}"
            })
        
        # After multiple failures, should implement rate limiting
        response = client.post("/auth/login", data={
            "username": "testuser",
            "password": "another-wrong-password"
        })
        
        # Should be rate limited or account locked
        assert response.status_code in [401, 429, 423]

    def test_session_security(self, client):
        """Test session security measures."""
        # Test session timeout
        with patch('main.get_current_user') as mock_get_user:
            mock_get_user.return_value = None  # Simulate expired session
            
            response = client.get("/auth/me", headers={
                "Authorization": "Bearer expired-session-token"
            })
            
            assert response.status_code == 401


@pytest.mark.security
class TestInputValidationSecurity:
    """Test input validation and sanitization."""
    
    def test_sql_injection_prevention(self, client):
        """Test SQL injection prevention."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'; DELETE FROM posts; --",
            "' UNION SELECT * FROM users --"
        ]
        
        for malicious_input in malicious_inputs:
            # Test in search endpoint
            response = client.get(f"/blog/search?q={malicious_input}")
            assert response.status_code in [200, 400, 422]
            
            # Test in blog post creation
            with patch('main.get_current_user') as mock_get_user:
                mock_get_user.return_value = {"is_admin": True}
                
                response = client.post("/blog/posts", 
                                     json={"title": malicious_input, "content": "test"},
                                     headers={"Authorization": "Bearer admin-token"})
                
                if response.status_code == 201:
                    # If accepted, ensure it's properly escaped
                    data = response.json()
                    assert "DROP TABLE" not in data.get("title", "")

    def test_xss_prevention(self, client):
        """Test XSS attack prevention."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<iframe src=javascript:alert('xss')></iframe>",
            "<svg onload=alert('xss')>"
        ]
        
        for payload in xss_payloads:
            with patch('main.get_current_user') as mock_get_user:
                mock_get_user.return_value = {"is_admin": True}
                
                response = client.post("/blog/posts", 
                                     json={"title": payload, "content": payload},
                                     headers={"Authorization": "Bearer admin-token"})
                
                if response.status_code == 201:
                    data = response.json()
                    # Ensure XSS payloads are sanitized
                    assert "<script>" not in data.get("title", "")
                    assert "javascript:" not in data.get("content", "")
                    assert "onerror=" not in data.get("content", "")

    def test_path_traversal_prevention(self, client):
        """Test path traversal attack prevention."""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc/passwd"
        ]
        
        for path in malicious_paths:
            # Test in file upload endpoints if they exist
            response = client.get(f"/files/{path}")
            assert response.status_code in [400, 404, 403]

    def test_command_injection_prevention(self, client):
        """Test command injection prevention."""
        command_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /",
            "`whoami`",
            "$(id)"
        ]
        
        for payload in command_payloads:
            # Test in any endpoint that might process system commands
            response = client.post("/api/webhook", 
                                 json={"command": payload})
            
            # Should not execute system commands
            assert response.status_code in [400, 403, 422]


@pytest.mark.security
class TestWebhookSecurity:
    """Test webhook security validation."""
    
    def test_webhook_signature_validation(self, webhook_validator):
        """Test webhook signature validation."""
        payload = '{"event": "push", "data": "test"}'
        
        # Test with valid signature
        signature = webhook_validator.generate_signature(payload)
        assert webhook_validator.validate_signature(payload, signature) is True
        
        # Test with invalid signature
        assert webhook_validator.validate_signature(payload, "invalid-signature") is False
        
        # Test with tampered payload
        tampered_payload = '{"event": "push", "data": "tampered"}'
        assert webhook_validator.validate_signature(tampered_payload, signature) is False

    def test_advanced_webhook_validation(self, advanced_webhook_validator):
        """Test advanced webhook validation features."""
        payload = '{"event": "push", "timestamp": 1234567890}'
        
        # Test timestamp validation
        old_timestamp = int(datetime.now().timestamp()) - 7200  # 2 hours ago
        old_payload = f'{{"event": "push", "timestamp": {old_timestamp}}}'
        
        signature = advanced_webhook_validator.generate_signature(old_payload)
        result = advanced_webhook_validator.validate_request(old_payload, signature)
        
        assert result["valid"] is False
        assert "timestamp" in result["error"].lower()

    def test_webhook_replay_attack_prevention(self, advanced_webhook_validator):
        """Test prevention of webhook replay attacks."""
        payload = '{"event": "push", "nonce": "unique-123"}'
        signature = advanced_webhook_validator.generate_signature(payload)
        
        # First request should succeed
        result1 = advanced_webhook_validator.validate_request(payload, signature)
        assert result1["valid"] is True
        
        # Replay should be detected and rejected
        result2 = advanced_webhook_validator.validate_request(payload, signature)
        assert result2["valid"] is False
        assert "replay" in result2["error"].lower()


@pytest.mark.security
class TestAuthorizationSecurity:
    """Test authorization and access control."""
    
    def test_admin_only_endpoints(self, client):
        """Test that admin-only endpoints are properly protected."""
        admin_endpoints = [
            "/admin/users",
            "/admin/posts",
            "/admin/analytics",
            "/api/keys"
        ]
        
        # Test without authentication
        for endpoint in admin_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
        
        # Test with regular user token
        with patch('main.get_current_user') as mock_get_user:
            mock_get_user.return_value = {"is_admin": False}
            
            for endpoint in admin_endpoints:
                response = client.get(endpoint, headers={
                    "Authorization": "Bearer user-token"
                })
                assert response.status_code == 403

    def test_user_data_isolation(self, client):
        """Test that users can only access their own data."""
        with patch('main.get_current_user') as mock_get_user:
            mock_get_user.return_value = {"id": "user-1", "is_admin": False}
            
            # Try to access another user's data
            response = client.get("/users/user-2/profile", headers={
                "Authorization": "Bearer user-1-token"
            })
            
            assert response.status_code in [403, 404]

    def test_api_key_permissions(self, client):
        """Test API key permission restrictions."""
        # Test with limited API key
        response = client.get("/api/posts", headers={
            "X-API-Key": "limited-read-only-key"
        })
        assert response.status_code == 200
        
        # Test write operation with read-only key
        response = client.post("/api/posts", 
                             json={"title": "test", "content": "test"},
                             headers={"X-API-Key": "limited-read-only-key"})
        assert response.status_code == 403


@pytest.mark.security
class TestSecurityHeaders:
    """Test security headers implementation."""
    
    def test_security_headers_present(self, client):
        """Test that required security headers are present."""
        response = client.get("/")
        
        headers = response.headers
        
        # Test HTTPS enforcement
        assert "Strict-Transport-Security" in headers
        
        # Test Content Security Policy
        assert "Content-Security-Policy" in headers
        
        # Test XSS protection
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        
        # Test frame options
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] in ["DENY", "SAMEORIGIN"]

    def test_cors_configuration(self, client):
        """Test CORS configuration is secure."""
        response = client.options("/api/posts", headers={
            "Origin": "https://malicious-site.com"
        })
        
        # Should not allow arbitrary origins
        cors_origin = response.headers.get("Access-Control-Allow-Origin")
        assert cors_origin != "*" or cors_origin is None


@pytest.mark.security
class TestDataProtection:
    """Test data protection and privacy measures."""
    
    def test_sensitive_data_exposure(self, client):
        """Test that sensitive data is not exposed in responses."""
        # Test user endpoint doesn't expose passwords
        with patch('main.get_current_user') as mock_get_user:
            mock_get_user.return_value = {"id": "user-1", "username": "test"}
            
            response = client.get("/auth/me", headers={
                "Authorization": "Bearer valid-token"
            })
            
            if response.status_code == 200:
                data = response.json()
                assert "password" not in data
                assert "password_hash" not in data
                assert "secret" not in data

    def test_error_message_information_disclosure(self, client):
        """Test that error messages don't disclose sensitive information."""
        # Test with non-existent user
        response = client.post("/auth/login", data={
            "username": "nonexistent@example.com",
            "password": "password"
        })
        
        error_message = response.json().get("detail", "")
        
        # Should not reveal whether user exists
        assert "user not found" not in error_message.lower()
        assert "invalid credentials" in error_message.lower()

    def test_logging_security(self, client):
        """Test that sensitive data is not logged."""
        with patch('main.logger') as mock_logger:
            # Make request with sensitive data
            client.post("/auth/login", data={
                "username": "test@example.com",
                "password": "secret-password"
            })
            
            # Check that password is not in log calls
            for call in mock_logger.info.call_args_list:
                log_message = str(call)
                assert "secret-password" not in log_message
                assert "password" not in log_message.lower()


@pytest.mark.security
class TestRateLimitingSecurity:
    """Test rate limiting security measures."""
    
    def test_api_rate_limiting(self, client):
        """Test API rate limiting enforcement."""
        # Make rapid requests to test rate limiting
        responses = []
        for i in range(100):
            response = client.get("/api/posts")
            responses.append(response.status_code)
            if response.status_code == 429:
                break
        
        # Should hit rate limit
        assert 429 in responses

    def test_authentication_rate_limiting(self, client):
        """Test rate limiting on authentication endpoints."""
        # Rapid login attempts
        responses = []
        for i in range(20):
            response = client.post("/auth/login", data={
                "username": "test@example.com",
                "password": "wrong-password"
            })
            responses.append(response.status_code)
            if response.status_code == 429:
                break
        
        # Should implement rate limiting on auth endpoints
        assert 429 in responses


if __name__ == "__main__":
    pytest.main([__file__, "-v"])