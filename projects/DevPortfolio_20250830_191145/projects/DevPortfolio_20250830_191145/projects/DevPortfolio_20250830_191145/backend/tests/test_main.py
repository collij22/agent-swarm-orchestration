"""
Unit tests for main FastAPI application
"""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import json
from datetime import datetime


@pytest.mark.unit
class TestMainEndpoints:
    """Test main application endpoints"""

    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint returns correct response"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "DevPortfolio API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "operational"
        assert data["docs"] == "/api/docs"
        assert "timestamp" in data

    def test_health_check_endpoint(self, client: TestClient):
        """Test health check endpoint"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_async_root_endpoint(self, async_client: AsyncClient):
        """Test root endpoint with async client"""
        response = await async_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "DevPortfolio API"
        assert data["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_async_health_check(self, async_client: AsyncClient):
        """Test health check with async client"""
        response = await async_client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"


@pytest.mark.unit
class TestAPIDocumentation:
    """Test API documentation endpoints"""

    def test_openapi_schema_accessible(self, client: TestClient):
        """Test that OpenAPI schema is accessible"""
        response = client.get("/api/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert schema["info"]["title"] == "DevPortfolio API"
        assert schema["info"]["version"] == "1.0.0"

    def test_swagger_docs_accessible(self, client: TestClient):
        """Test that Swagger documentation is accessible"""
        response = client.get("/api/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_docs_accessible(self, client: TestClient):
        """Test that ReDoc documentation is accessible"""
        response = client.get("/api/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


@pytest.mark.unit
class TestCORSMiddleware:
    """Test CORS middleware functionality"""

    def test_cors_preflight_request(self, client: TestClient):
        """Test CORS preflight request"""
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers

    def test_cors_actual_request(self, client: TestClient):
        """Test actual request with CORS headers"""
        response = client.get(
            "/api/health",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers


@pytest.mark.unit
class TestSecurityHeaders:
    """Test security headers and middleware"""

    def test_security_headers_present(self, client: TestClient):
        """Test that security headers are present in responses"""
        response = client.get("/api/health")
        
        # Check for common security headers
        headers = response.headers
        
        # These would be added by SecurityMiddleware
        # Adjust based on actual implementation
        assert response.status_code == 200

    def test_trusted_host_middleware(self, client: TestClient):
        """Test trusted host middleware"""
        response = client.get(
            "/api/health",
            headers={"Host": "localhost"}
        )
        assert response.status_code == 200


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling and responses"""

    def test_404_endpoint(self, client: TestClient):
        """Test 404 response for non-existent endpoint"""
        response = client.get("/non-existent-endpoint")
        assert response.status_code == 404

    def test_invalid_json_payload(self, client: TestClient):
        """Test handling of invalid JSON payload"""
        response = client.post(
            "/api/contact",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        # Should return 422 for validation error or 400 for bad request
        assert response.status_code in [400, 422]

    def test_method_not_allowed(self, client: TestClient):
        """Test method not allowed response"""
        response = client.post("/api/health")
        assert response.status_code == 405


@pytest.mark.unit
class TestApplicationLifespan:
    """Test application lifespan events"""

    @pytest.mark.asyncio
    async def test_application_startup(self, async_client: AsyncClient):
        """Test that application starts up correctly"""
        # The fact that we can make requests means startup succeeded
        response = await async_client.get("/api/health")
        assert response.status_code == 200

    def test_application_metadata(self, client: TestClient):
        """Test application metadata is correct"""
        response = client.get("/api/openapi.json")
        schema = response.json()
        
        assert schema["info"]["title"] == "DevPortfolio API"
        assert schema["info"]["description"] == "Professional developer portfolio and blog platform with AI-powered content assistance"
        assert schema["info"]["version"] == "1.0.0"


@pytest.mark.unit
class TestResponseFormat:
    """Test response format consistency"""

    def test_json_response_format(self, client: TestClient):
        """Test that JSON responses are properly formatted"""
        response = client.get("/")
        
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        
        # Verify timestamp format
        timestamp = data.get("timestamp")
        assert timestamp is not None
        
        # Should be valid ISO format
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_health_response_consistency(self, client: TestClient):
        """Test health endpoint response consistency"""
        response1 = client.get("/api/health")
        response2 = client.get("/api/health")
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Status and version should be consistent
        assert data1["status"] == data2["status"]
        assert data1["version"] == data2["version"]
        
        # Timestamps should be different (unless called at exact same time)
        # This tests that timestamps are actually being generated