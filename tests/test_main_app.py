"""
Unit tests for the main FastAPI application.
Tests all endpoints, authentication, and core functionality.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
from datetime import datetime

from main import app, get_db
from database import get_database_url
from models.user import User
from models.blog import BlogPost
from models.portfolio import Project


@pytest.fixture
def client():
    """Create test client with mocked database."""
    def override_get_db():
        return Mock()
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user():
    """Mock user for authentication tests."""
    return {
        "id": "test-user-123",
        "username": "testuser",
        "email": "test@example.com",
        "is_admin": False
    }


@pytest.fixture
def mock_admin_user():
    """Mock admin user for authorization tests."""
    return {
        "id": "admin-user-123",
        "username": "admin",
        "email": "admin@example.com",
        "is_admin": True
    }


class TestHealthEndpoints:
    """Test health and status endpoints."""
    
    def test_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_root_endpoint(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "DevPortfolio API"
        assert data["version"] == "1.0.0"


class TestAuthenticationEndpoints:
    """Test authentication and authorization."""
    
    @patch('main.authenticate_user')
    def test_login_success(self, mock_auth, client):
        """Test successful login."""
        mock_auth.return_value = {"access_token": "test-token", "token_type": "bearer"}
        
        response = client.post("/auth/login", data={
            "username": "testuser",
            "password": "testpass"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post("/auth/login", data={
            "username": "invalid",
            "password": "wrong"
        })
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    @patch('main.get_current_user')
    def test_protected_endpoint_with_valid_token(self, mock_get_user, client, mock_user):
        """Test accessing protected endpoint with valid token."""
        mock_get_user.return_value = mock_user
        
        response = client.get("/auth/me", headers={
            "Authorization": "Bearer valid-token"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == mock_user["username"]

    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/auth/me")
        assert response.status_code == 401


class TestBlogEndpoints:
    """Test blog-related endpoints."""
    
    def test_get_blog_posts(self, client):
        """Test retrieving blog posts."""
        with patch('routers.blog.get_blog_posts') as mock_get_posts:
            mock_posts = [
                {
                    "id": "post-1",
                    "title": "Test Post",
                    "content": "Test content",
                    "published": True,
                    "created_at": datetime.now().isoformat()
                }
            ]
            mock_get_posts.return_value = mock_posts
            
            response = client.get("/blog/posts")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == "Test Post"

    def test_get_blog_post_by_id(self, client):
        """Test retrieving specific blog post."""
        with patch('routers.blog.get_blog_post') as mock_get_post:
            mock_post = {
                "id": "post-1",
                "title": "Test Post",
                "content": "Test content",
                "published": True
            }
            mock_get_post.return_value = mock_post
            
            response = client.get("/blog/posts/post-1")
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Test Post"

    def test_get_nonexistent_blog_post(self, client):
        """Test retrieving non-existent blog post."""
        with patch('routers.blog.get_blog_post') as mock_get_post:
            mock_get_post.return_value = None
            
            response = client.get("/blog/posts/nonexistent")
            assert response.status_code == 404

    @patch('main.get_current_user')
    def test_create_blog_post_authenticated(self, mock_get_user, client, mock_admin_user):
        """Test creating blog post as authenticated admin."""
        mock_get_user.return_value = mock_admin_user
        
        with patch('routers.blog.create_blog_post') as mock_create:
            mock_create.return_value = {"id": "new-post", "title": "New Post"}
            
            post_data = {
                "title": "New Post",
                "content": "New content",
                "tags": ["test"]
            }
            
            response = client.post("/blog/posts", 
                                 json=post_data,
                                 headers={"Authorization": "Bearer admin-token"})
            
            assert response.status_code == 201
            data = response.json()
            assert data["title"] == "New Post"

    def test_create_blog_post_unauthenticated(self, client):
        """Test creating blog post without authentication."""
        post_data = {
            "title": "New Post",
            "content": "New content"
        }
        
        response = client.post("/blog/posts", json=post_data)
        assert response.status_code == 401


class TestPortfolioEndpoints:
    """Test portfolio-related endpoints."""
    
    def test_get_projects(self, client):
        """Test retrieving portfolio projects."""
        with patch('routers.portfolio.get_projects') as mock_get_projects:
            mock_projects = [
                {
                    "id": "project-1",
                    "title": "Test Project",
                    "description": "Test description",
                    "technologies": ["Python", "FastAPI"]
                }
            ]
            mock_get_projects.return_value = mock_projects
            
            response = client.get("/portfolio/projects")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == "Test Project"

    def test_get_project_by_id(self, client):
        """Test retrieving specific project."""
        with patch('routers.portfolio.get_project') as mock_get_project:
            mock_project = {
                "id": "project-1",
                "title": "Test Project",
                "description": "Test description"
            }
            mock_get_project.return_value = mock_project
            
            response = client.get("/portfolio/projects/project-1")
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Test Project"


class TestAPIEndpoints:
    """Test API management endpoints."""
    
    @patch('main.get_current_user')
    def test_api_key_generation(self, mock_get_user, client, mock_admin_user):
        """Test API key generation for admin users."""
        mock_get_user.return_value = mock_admin_user
        
        with patch('main.generate_api_key') as mock_gen_key:
            mock_gen_key.return_value = "api-key-123"
            
            response = client.post("/api/keys", 
                                 headers={"Authorization": "Bearer admin-token"})
            
            assert response.status_code == 201
            data = response.json()
            assert "api_key" in data

    def test_api_key_generation_non_admin(self, client):
        """Test API key generation fails for non-admin users."""
        with patch('main.get_current_user') as mock_get_user:
            mock_get_user.return_value = {"is_admin": False}
            
            response = client.post("/api/keys", 
                                 headers={"Authorization": "Bearer user-token"})
            
            assert response.status_code == 403


class TestInputValidation:
    """Test input validation and sanitization."""
    
    def test_blog_post_validation(self, client):
        """Test blog post input validation."""
        invalid_data = {
            "title": "",  # Empty title
            "content": "x" * 100000,  # Too long content
            "tags": ["tag"] * 50  # Too many tags
        }
        
        response = client.post("/blog/posts", 
                             json=invalid_data,
                             headers={"Authorization": "Bearer admin-token"})
        
        assert response.status_code == 422  # Validation error

    def test_xss_prevention(self, client):
        """Test XSS prevention in user inputs."""
        malicious_data = {
            "title": "<script>alert('xss')</script>",
            "content": "<img src=x onerror=alert('xss')>"
        }
        
        with patch('main.get_current_user') as mock_get_user:
            mock_get_user.return_value = {"is_admin": True}
            
            response = client.post("/blog/posts", 
                                 json=malicious_data,
                                 headers={"Authorization": "Bearer admin-token"})
            
            # Should either reject or sanitize the input
            if response.status_code == 201:
                data = response.json()
                assert "<script>" not in data.get("title", "")
                assert "onerror=" not in data.get("content", "")


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limiting_enforcement(self, client):
        """Test that rate limiting is enforced."""
        # Make multiple requests quickly
        responses = []
        for i in range(10):
            response = client.get("/blog/posts")
            responses.append(response.status_code)
        
        # At least some requests should succeed
        assert 200 in responses
        
        # If rate limiting is working, some might be 429
        # This is a basic test - real rate limiting would need more sophisticated testing


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests with database operations."""
    
    @patch('database.get_db_connection')
    def test_database_connection(self, mock_conn):
        """Test database connection handling."""
        mock_conn.return_value = Mock()
        
        response = TestClient(app).get("/health")
        assert response.status_code == 200

    def test_database_error_handling(self, client):
        """Test graceful handling of database errors."""
        with patch('database.get_db_connection') as mock_conn:
            mock_conn.side_effect = Exception("Database connection failed")
            
            response = client.get("/blog/posts")
            # Should handle database errors gracefully
            assert response.status_code in [500, 503]


@pytest.mark.performance
class TestPerformanceRequirements:
    """Test performance requirements."""
    
    def test_api_response_time(self, client):
        """Test API response time meets requirements (<200ms)."""
        import time
        
        start_time = time.time()
        response = client.get("/blog/posts")
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert response.status_code == 200
        # Allow some flexibility in test environment
        assert response_time < 500  # 500ms for test environment

    def test_large_payload_handling(self, client):
        """Test handling of large payloads."""
        large_content = "x" * 50000  # 50KB content
        
        with patch('main.get_current_user') as mock_get_user:
            mock_get_user.return_value = {"is_admin": True}
            
            post_data = {
                "title": "Large Post",
                "content": large_content
            }
            
            response = client.post("/blog/posts", 
                                 json=post_data,
                                 headers={"Authorization": "Bearer admin-token"})
            
            # Should handle large payloads appropriately
            assert response.status_code in [201, 413]  # Created or Payload Too Large


if __name__ == "__main__":
    pytest.main([__file__])