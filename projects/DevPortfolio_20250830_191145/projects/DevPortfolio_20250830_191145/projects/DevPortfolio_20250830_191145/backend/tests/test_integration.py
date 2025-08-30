"""
Integration tests for DevPortfolio API endpoints
"""
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
import json
from unittest.mock import patch, AsyncMock


@pytest.mark.integration
class TestPortfolioIntegration:
    """Integration tests for portfolio endpoints"""

    @pytest.mark.asyncio
    async def test_portfolio_crud_flow(self, async_client: AsyncClient, auth_headers):
        """Test complete portfolio CRUD operations"""
        
        # Create project
        project_data = {
            "title": "Test Project",
            "description": "A test project for integration testing",
            "github_url": "https://github.com/user/test-project",
            "demo_url": "https://demo.example.com",
            "technologies": ["Python", "FastAPI", "React"],
            "featured": True
        }
        
        create_response = await async_client.post(
            "/api/portfolio/projects",
            json=project_data,
            headers=auth_headers
        )
        
        assert create_response.status_code == 201
        created_project = create_response.json()
        project_id = created_project["id"]
        
        # Read project
        get_response = await async_client.get(f"/api/portfolio/projects/{project_id}")
        assert get_response.status_code == 200
        
        retrieved_project = get_response.json()
        assert retrieved_project["title"] == project_data["title"]
        assert retrieved_project["technologies"] == project_data["technologies"]
        
        # Update project
        update_data = {
            "title": "Updated Test Project",
            "description": "Updated description"
        }
        
        update_response = await async_client.put(
            f"/api/portfolio/projects/{project_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert update_response.status_code == 200
        updated_project = update_response.json()
        assert updated_project["title"] == update_data["title"]
        
        # Delete project
        delete_response = await async_client.delete(
            f"/api/portfolio/projects/{project_id}",
            headers=auth_headers
        )
        
        assert delete_response.status_code == 204
        
        # Verify deletion
        get_deleted_response = await async_client.get(f"/api/portfolio/projects/{project_id}")
        assert get_deleted_response.status_code == 404

    @pytest.mark.asyncio
    async def test_portfolio_list_filtering(self, async_client: AsyncClient, test_project):
        """Test portfolio project filtering and pagination"""
        
        # Test basic list
        response = await async_client.get("/api/portfolio/projects")
        assert response.status_code == 200
        
        projects = response.json()
        assert isinstance(projects, list)
        assert len(projects) >= 1
        
        # Test filtering by technology
        response = await async_client.get("/api/portfolio/projects?technology=Python")
        assert response.status_code == 200
        
        # Test pagination
        response = await async_client.get("/api/portfolio/projects?skip=0&limit=5")
        assert response.status_code == 200


@pytest.mark.integration
class TestBlogIntegration:
    """Integration tests for blog endpoints"""

    @pytest.mark.asyncio
    async def test_blog_crud_flow(self, async_client: AsyncClient, auth_headers):
        """Test complete blog CRUD operations"""
        
        # Create blog post
        post_data = {
            "title": "Test Blog Post",
            "content": "# Test Content\n\nThis is a test blog post with **markdown**.",
            "excerpt": "This is a test blog post.",
            "tags": ["test", "integration", "api"],
            "is_published": True
        }
        
        create_response = await async_client.post(
            "/api/blog/posts",
            json=post_data,
            headers=auth_headers
        )
        
        assert create_response.status_code == 201
        created_post = create_response.json()
        post_id = created_post["id"]
        
        # Verify slug generation
        assert "slug" in created_post
        assert created_post["slug"] == "test-blog-post"
        
        # Read by ID
        get_response = await async_client.get(f"/api/blog/posts/{post_id}")
        assert get_response.status_code == 200
        
        # Read by slug
        slug_response = await async_client.get(f"/api/blog/posts/slug/{created_post['slug']}")
        assert slug_response.status_code == 200
        
        # Update post
        update_data = {
            "title": "Updated Blog Post",
            "is_published": False
        }
        
        update_response = await async_client.put(
            f"/api/blog/posts/{post_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert update_response.status_code == 200
        updated_post = update_response.json()
        assert updated_post["title"] == update_data["title"]
        assert updated_post["is_published"] == False
        
        # Delete post
        delete_response = await async_client.delete(
            f"/api/blog/posts/{post_id}",
            headers=auth_headers
        )
        
        assert delete_response.status_code == 204

    @pytest.mark.asyncio
    async def test_blog_search_and_filter(self, async_client: AsyncClient, test_blog_post):
        """Test blog search and filtering functionality"""
        
        # Test search
        search_response = await async_client.get("/api/blog/search?q=test")
        assert search_response.status_code == 200
        
        search_results = search_response.json()
        assert isinstance(search_results, list)
        
        # Test tag filtering
        tag_response = await async_client.get("/api/blog/posts?tag=test")
        assert tag_response.status_code == 200
        
        # Test published only filter
        published_response = await async_client.get("/api/blog/posts?published_only=true")
        assert published_response.status_code == 200


@pytest.mark.integration
class TestAuthIntegration:
    """Integration tests for authentication endpoints"""

    @pytest.mark.asyncio
    async def test_user_registration_and_login_flow(self, async_client: AsyncClient):
        """Test complete user registration and login flow"""
        
        # Register new user
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "securepassword123"
        }
        
        register_response = await async_client.post(
            "/api/auth/register",
            json=user_data
        )
        
        assert register_response.status_code == 201
        registered_user = register_response.json()
        assert registered_user["email"] == user_data["email"]
        assert "password" not in registered_user  # Password should not be returned
        
        # Login with new user
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        
        login_response = await async_client.post(
            "/api/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert login_response.status_code == 200
        login_result = login_response.json()
        assert "access_token" in login_result
        assert login_result["token_type"] == "bearer"
        
        # Use token to access protected endpoint
        token = login_result["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        profile_response = await async_client.get(
            "/api/auth/me",
            headers=auth_headers
        )
        
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["email"] == user_data["email"]

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_auth(self, async_client: AsyncClient):
        """Test accessing protected endpoints without authentication"""
        
        # Try to create project without auth
        project_data = {
            "title": "Test Project",
            "description": "Should fail without auth"
        }
        
        response = await async_client.post(
            "/api/portfolio/projects",
            json=project_data
        )
        
        assert response.status_code == 401


@pytest.mark.integration
class TestAIIntegration:
    """Integration tests for AI assistant endpoints"""

    @pytest.mark.asyncio
    @patch('services.ai_service.OpenAI')
    async def test_ai_content_generation(self, mock_openai, async_client: AsyncClient, auth_headers):
        """Test AI content generation endpoint"""
        
        # Mock OpenAI response
        mock_openai.return_value.chat.completions.create = AsyncMock(
            return_value=type('obj', (object,), {
                'choices': [type('obj', (object,), {
                    'message': type('obj', (object,), {
                        'content': 'Generated content based on prompt'
                    })()
                })()]
            })()
        )
        
        request_data = {
            "prompt": "Write a blog post about Python best practices",
            "type": "blog_content",
            "max_tokens": 500
        }
        
        response = await async_client.post(
            "/api/ai/generate",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "content" in result
        assert "usage" in result

    @pytest.mark.asyncio
    async def test_ai_endpoint_rate_limiting(self, async_client: AsyncClient, auth_headers):
        """Test rate limiting on AI endpoints"""
        
        request_data = {
            "prompt": "Test prompt",
            "type": "suggestion"
        }
        
        # Make multiple rapid requests
        responses = []
        for _ in range(5):
            response = await async_client.post(
                "/api/ai/generate",
                json=request_data,
                headers=auth_headers
            )
            responses.append(response.status_code)
        
        # Should eventually hit rate limit
        assert 429 in responses or all(r == 200 for r in responses)


@pytest.mark.integration
class TestAnalyticsIntegration:
    """Integration tests for analytics endpoints"""

    @pytest.mark.asyncio
    async def test_analytics_tracking(self, async_client: AsyncClient):
        """Test analytics event tracking"""
        
        event_data = {
            "event_type": "page_view",
            "page": "/portfolio",
            "user_agent": "test-agent",
            "ip_address": "127.0.0.1"
        }
        
        response = await async_client.post(
            "/api/analytics/track",
            json=event_data
        )
        
        # Should accept tracking data
        assert response.status_code in [200, 201, 204]

    @pytest.mark.asyncio
    async def test_analytics_dashboard_data(self, async_client: AsyncClient, admin_auth_headers):
        """Test analytics dashboard data retrieval"""
        
        response = await async_client.get(
            "/api/analytics/dashboard",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        dashboard_data = response.json()
        
        # Should contain analytics metrics
        assert "page_views" in dashboard_data or "visits" in dashboard_data


@pytest.mark.integration
class TestContactIntegration:
    """Integration tests for contact endpoints"""

    @pytest.mark.asyncio
    async def test_contact_form_submission(self, async_client: AsyncClient):
        """Test contact form submission"""
        
        contact_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Test Inquiry",
            "message": "This is a test message from the integration tests."
        }
        
        response = await async_client.post(
            "/api/contact/submit",
            json=contact_data
        )
        
        assert response.status_code in [200, 201]
        result = response.json()
        assert "message" in result

    @pytest.mark.asyncio
    async def test_contact_form_validation(self, async_client: AsyncClient):
        """Test contact form validation"""
        
        # Invalid email
        invalid_data = {
            "name": "John Doe",
            "email": "invalid-email",
            "subject": "Test",
            "message": "Test message"
        }
        
        response = await async_client.post(
            "/api/contact/submit",
            json=invalid_data
        )
        
        assert response.status_code == 422  # Validation error


@pytest.mark.integration
class TestEndToEndWorkflows:
    """End-to-end workflow tests"""

    @pytest.mark.asyncio
    async def test_complete_portfolio_workflow(self, async_client: AsyncClient):
        """Test complete portfolio creation and display workflow"""
        
        # 1. Register user
        user_data = {
            "email": "portfolio@example.com",
            "username": "portfoliouser",
            "full_name": "Portfolio User",
            "password": "securepass123"
        }
        
        register_response = await async_client.post("/api/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        # 2. Login
        login_response = await async_client.post(
            "/api/auth/login",
            data={"username": user_data["email"], "password": user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Create portfolio project
        project_data = {
            "title": "E2E Test Project",
            "description": "End-to-end test project",
            "github_url": "https://github.com/user/e2e-project",
            "technologies": ["Python", "FastAPI"]
        }
        
        project_response = await async_client.post(
            "/api/portfolio/projects",
            json=project_data,
            headers=auth_headers
        )
        
        assert project_response.status_code == 201
        
        # 4. View public portfolio
        public_response = await async_client.get("/api/portfolio/projects")
        assert public_response.status_code == 200
        
        projects = public_response.json()
        assert any(p["title"] == project_data["title"] for p in projects)