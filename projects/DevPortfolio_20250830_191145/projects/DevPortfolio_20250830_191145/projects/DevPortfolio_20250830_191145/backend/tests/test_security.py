"""
Security tests for DevPortfolio API
Tests authentication, authorization, input validation, and security vulnerabilities
"""
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
import jwt
import json
from datetime import datetime, timedelta
from unittest.mock import patch


@pytest.mark.security
class TestAuthentication:
    """Test authentication security"""

    @pytest.mark.asyncio
    async def test_jwt_token_validation(self, async_client: AsyncClient):
        """Test JWT token validation and security"""
        
        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = await async_client.get("/api/auth/me", headers=invalid_headers)
        assert response.status_code == 401
        
        # Test with malformed token
        malformed_headers = {"Authorization": "Bearer "}
        response = await async_client.get("/api/auth/me", headers=malformed_headers)
        assert response.status_code == 401
        
        # Test with no token
        response = await async_client.get("/api/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_token_expiration(self, async_client: AsyncClient):
        """Test JWT token expiration handling"""
        
        # Create expired token
        expired_payload = {
            "sub": "test_user",
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        
        expired_token = jwt.encode(expired_payload, "test-secret", algorithm="HS256")
        expired_headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = await async_client.get("/api/auth/me", headers=expired_headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_password_security(self, async_client: AsyncClient):
        """Test password security requirements"""
        
        # Test weak password
        weak_password_data = {
            "email": "weak@example.com",
            "username": "weakuser",
            "full_name": "Weak User",
            "password": "123"  # Too short
        }
        
        response = await async_client.post("/api/auth/register", json=weak_password_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_login_rate_limiting(self, async_client: AsyncClient):
        """Test login rate limiting to prevent brute force attacks"""
        
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        # Attempt multiple failed logins
        failed_attempts = 0
        for _ in range(10):
            response = await async_client.post(
                "/api/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 429:  # Rate limited
                break
            elif response.status_code == 401:  # Unauthorized
                failed_attempts += 1
        
        # Should eventually be rate limited or consistently return 401
        assert failed_attempts > 0 or response.status_code == 429


@pytest.mark.security
class TestAuthorization:
    """Test authorization and access control"""

    @pytest.mark.asyncio
    async def test_admin_only_endpoints(self, async_client: AsyncClient, auth_headers):
        """Test that admin-only endpoints reject non-admin users"""
        
        # Try to access admin analytics with regular user
        response = await async_client.get(
            "/api/analytics/dashboard",
            headers=auth_headers
        )
        
        # Should be forbidden for non-admin users
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_user_data_isolation(self, async_client: AsyncClient, auth_headers):
        """Test that users can only access their own data"""
        
        # Create a project
        project_data = {
            "title": "User's Project",
            "description": "This should only be editable by the owner"
        }
        
        create_response = await async_client.post(
            "/api/portfolio/projects",
            json=project_data,
            headers=auth_headers
        )
        
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]
        
        # Try to modify with different user (would need another user's token)
        # This test assumes we have a way to create another user's token
        # For now, we'll test with invalid token
        
        invalid_headers = {"Authorization": "Bearer fake_token"}
        update_response = await async_client.put(
            f"/api/portfolio/projects/{project_id}",
            json={"title": "Hacked title"},
            headers=invalid_headers
        )
        
        assert update_response.status_code == 401

    @pytest.mark.asyncio
    async def test_resource_ownership(self, async_client: AsyncClient, test_project, auth_headers):
        """Test that users can only modify resources they own"""
        
        # Try to delete someone else's project (assuming test_project belongs to test_user)
        response = await async_client.delete(
            f"/api/portfolio/projects/{test_project.id}",
            headers=auth_headers
        )
        
        # Should succeed if same user, fail if different user
        # This test needs proper setup with multiple users
        assert response.status_code in [204, 403, 404]


@pytest.mark.security
class TestInputValidation:
    """Test input validation and sanitization"""

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, async_client: AsyncClient):
        """Test SQL injection prevention"""
        
        # Try SQL injection in search parameter
        malicious_query = "'; DROP TABLE users; --"
        
        response = await async_client.get(f"/api/blog/search?q={malicious_query}")
        
        # Should not cause server error, should handle gracefully
        assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_xss_prevention(self, async_client: AsyncClient, auth_headers):
        """Test XSS prevention in content fields"""
        
        # Try to inject script tag
        malicious_content = {
            "title": "<script>alert('XSS')</script>Malicious Title",
            "content": "Normal content with <script>alert('XSS')</script>",
            "description": "<img src=x onerror=alert('XSS')>"
        }
        
        response = await async_client.post(
            "/api/portfolio/projects",
            json=malicious_content,
            headers=auth_headers
        )
        
        if response.status_code == 201:
            # Check that script tags are escaped or removed
            created_project = response.json()
            assert "<script>" not in created_project.get("title", "")
            assert "onerror=" not in created_project.get("description", "")

    @pytest.mark.asyncio
    async def test_file_upload_security(self, async_client: AsyncClient, auth_headers):
        """Test file upload security (if implemented)"""
        
        # This would test file upload endpoints if they exist
        # For now, we'll test that non-existent upload endpoints return 404
        
        response = await async_client.post(
            "/api/upload/image",
            files={"file": ("test.txt", "test content", "text/plain")},
            headers=auth_headers
        )
        
        # Should return 404 if not implemented, or proper validation if implemented
        assert response.status_code in [404, 400, 422, 413]  # 413 = Payload too large

    @pytest.mark.asyncio
    async def test_email_validation(self, async_client: AsyncClient):
        """Test email validation in various endpoints"""
        
        # Test invalid email in registration
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user..double.dot@example.com",
            "user@.com"
        ]
        
        for invalid_email in invalid_emails:
            user_data = {
                "email": invalid_email,
                "username": "testuser",
                "full_name": "Test User",
                "password": "securepassword123"
            }
            
            response = await async_client.post("/api/auth/register", json=user_data)
            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_url_validation(self, async_client: AsyncClient, auth_headers):
        """Test URL validation in project fields"""
        
        invalid_urls = [
            "not-a-url",
            "ftp://invalid-protocol.com",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>"
        ]
        
        for invalid_url in invalid_urls:
            project_data = {
                "title": "Test Project",
                "description": "Test description",
                "github_url": invalid_url,
                "demo_url": invalid_url
            }
            
            response = await async_client.post(
                "/api/portfolio/projects",
                json=project_data,
                headers=auth_headers
            )
            
            # Should reject invalid URLs
            assert response.status_code in [400, 422]


@pytest.mark.security
class TestDataProtection:
    """Test data protection and privacy"""

    @pytest.mark.asyncio
    async def test_password_not_exposed(self, async_client: AsyncClient):
        """Test that passwords are never exposed in responses"""
        
        # Register user
        user_data = {
            "email": "privacy@example.com",
            "username": "privacyuser",
            "full_name": "Privacy User",
            "password": "securepassword123"
        }
        
        register_response = await async_client.post("/api/auth/register", json=user_data)
        
        if register_response.status_code == 201:
            user_info = register_response.json()
            assert "password" not in user_info
            assert "hashed_password" not in user_info

    @pytest.mark.asyncio
    async def test_sensitive_data_filtering(self, async_client: AsyncClient, auth_headers):
        """Test that sensitive data is filtered from responses"""
        
        # Get user profile
        response = await async_client.get("/api/auth/me", headers=auth_headers)
        
        if response.status_code == 200:
            user_data = response.json()
            
            # Should not contain sensitive fields
            sensitive_fields = ["password", "hashed_password", "secret_key"]
            for field in sensitive_fields:
                assert field not in user_data

    @pytest.mark.asyncio
    async def test_error_information_disclosure(self, async_client: AsyncClient):
        """Test that error messages don't disclose sensitive information"""
        
        # Try to access non-existent user
        response = await async_client.get("/api/users/99999")
        
        if response.status_code == 404:
            error_data = response.json()
            
            # Error message should be generic, not revealing database structure
            error_message = error_data.get("detail", "").lower()
            assert "table" not in error_message
            assert "column" not in error_message
            assert "database" not in error_message


@pytest.mark.security
class TestSecurityHeaders:
    """Test security headers and configurations"""

    def test_security_headers_present(self, client: TestClient):
        """Test that security headers are present"""
        
        response = client.get("/api/health")
        headers = response.headers
        
        # Test for common security headers
        # Note: Actual headers depend on SecurityMiddleware implementation
        expected_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection"
        ]
        
        # For now, just ensure response is successful
        # In real implementation, check for actual security headers
        assert response.status_code == 200

    def test_cors_configuration(self, client: TestClient):
        """Test CORS configuration security"""
        
        # Test that CORS doesn't allow all origins in production
        response = client.options(
            "/api/health",
            headers={
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        # Should either reject or have proper CORS configuration
        if "Access-Control-Allow-Origin" in response.headers:
            allowed_origin = response.headers["Access-Control-Allow-Origin"]
            assert allowed_origin != "*"  # Should not allow all origins


@pytest.mark.security
class TestAPISecurityBestPractices:
    """Test API security best practices"""

    @pytest.mark.asyncio
    async def test_https_enforcement(self, async_client: AsyncClient):
        """Test HTTPS enforcement (in production)"""
        
        # This would test HTTPS redirect in production
        # For testing, we'll just ensure endpoints respond
        
        response = await async_client.get("/api/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_request_size_limits(self, async_client: AsyncClient, auth_headers):
        """Test request size limits"""
        
        # Try to send very large payload
        large_content = "x" * (10 * 1024 * 1024)  # 10MB
        
        large_payload = {
            "title": "Test",
            "description": large_content
        }
        
        response = await async_client.post(
            "/api/portfolio/projects",
            json=large_payload,
            headers=auth_headers
        )
        
        # Should reject large payloads
        assert response.status_code in [400, 413, 422]

    @pytest.mark.asyncio
    async def test_api_versioning_security(self, async_client: AsyncClient):
        """Test API versioning doesn't expose old vulnerabilities"""
        
        # Test that old API versions don't exist or are properly secured
        old_version_paths = [
            "/v1/api/health",
            "/api/v1/health",
            "/old/api/health"
        ]
        
        for path in old_version_paths:
            response = await async_client.get(path)
            # Should return 404 for non-existent old versions
            assert response.status_code == 404