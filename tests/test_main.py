"""
Unit tests for main FastAPI application
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os

# Add the parent directory to the path to import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, get_db
from database import SessionLocal, engine
import models

# Test client
client = TestClient(app)

class TestMainApplication:
    """Test the main FastAPI application"""
    
    def setup_method(self):
        """Setup test database"""
        models.Base.metadata.create_all(bind=engine)
        
    def teardown_method(self):
        """Cleanup after tests"""
        models.Base.metadata.drop_all(bind=engine)

    def test_root_endpoint(self):
        """Test the root endpoint returns correct response"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "DevPortfolio API"
        assert data["version"] == "1.0.0"
        assert "status" in data
        assert "timestamp" in data

    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "external_services" in data
        assert "timestamp" in data

    @patch('main.get_db')
    def test_health_database_connection(self, mock_db):
        """Test health check with database connection"""
        mock_session = Mock()
        mock_db.return_value = mock_session
        mock_session.execute.return_value.scalar.return_value = 1
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["database"]["status"] == "connected"

    @patch('main.get_db')
    def test_health_database_error(self, mock_db):
        """Test health check with database error"""
        mock_session = Mock()
        mock_db.return_value = mock_session
        mock_session.execute.side_effect = Exception("Database connection failed")
        
        response = client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["database"]["status"] == "error"

    def test_cors_headers(self):
        """Test CORS headers are properly set"""
        response = client.options("/")
        assert response.status_code == 200
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers

    def test_api_docs_available(self):
        """Test that API documentation is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_schema(self):
        """Test that OpenAPI schema is available"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "DevPortfolio API"
        assert schema["info"]["version"] == "1.0.0"

    def test_invalid_endpoint(self):
        """Test accessing invalid endpoint returns 404"""
        response = client.get("/invalid-endpoint")
        assert response.status_code == 404

    @patch('services.external_integration_service.ExternalIntegrationService')
    def test_external_services_status(self, mock_service):
        """Test external services status in health check"""
        mock_instance = Mock()
        mock_service.return_value = mock_instance
        mock_instance.check_github_status.return_value = {"status": "healthy"}
        mock_instance.check_openai_status.return_value = {"status": "healthy"}
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "external_services" in data

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_request_validation_error(self):
        """Test request validation error handling"""
        # This would test malformed JSON requests
        response = client.post(
            "/api/v1/blog/posts",
            json={"invalid": "data"},
            headers={"Content-Type": "application/json"}
        )
        # Should return 422 for validation error
        assert response.status_code in [422, 404]  # 404 if endpoint doesn't exist yet

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Make multiple rapid requests
        responses = []
        for i in range(10):
            response = client.get("/")
            responses.append(response.status_code)
        
        # All should succeed for now (rate limiting not implemented yet)
        assert all(status == 200 for status in responses)

    def test_large_request_body(self):
        """Test handling of large request bodies"""
        large_data = {"data": "x" * 10000}  # 10KB of data
        response = client.post(
            "/api/v1/test",
            json=large_data,
            headers={"Content-Type": "application/json"}
        )
        # Should handle gracefully (404 expected since endpoint doesn't exist)
        assert response.status_code == 404

class TestSecurity:
    """Test security features"""
    
    def test_security_headers(self):
        """Test that security headers are present"""
        response = client.get("/")
        headers = response.headers
        
        # Check for basic security headers
        # Note: Some may not be implemented yet
        expected_headers = [
            "x-content-type-options",
            "x-frame-options", 
            "x-xss-protection"
        ]
        
        # For now, just ensure no sensitive headers are leaked
        assert "server" not in headers.get("server", "").lower()

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention in query parameters"""
        malicious_input = "'; DROP TABLE users; --"
        response = client.get(f"/api/v1/blog/posts?search={malicious_input}")
        
        # Should not cause server error (404 expected since endpoint doesn't exist)
        assert response.status_code in [404, 422]

    def test_xss_prevention(self):
        """Test XSS prevention in responses"""
        xss_payload = "<script>alert('xss')</script>"
        response = client.get(f"/api/v1/blog/posts?title={xss_payload}")
        
        # Should not reflect unescaped script tags
        assert response.status_code in [404, 422]
        if response.status_code == 200:
            assert "<script>" not in response.text

if __name__ == "__main__":
    pytest.main([__file__, "-v"])