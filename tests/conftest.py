"""
DevPortfolio Test Configuration
Comprehensive pytest configuration for testing all components
"""
import os
import sys
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import redis
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import application modules
try:
    from main import app
    from database import Base, get_db, get_redis
    from models.base import BaseModel
    from models.user import User
    from models.blog import BlogPost, BlogCategory
    from models.portfolio import Project, Skill
    from models.analytics import PageView, Visitor
    from models.contact import ContactSubmission
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")
    # Create mock app for testing
    from fastapi import FastAPI
    app = FastAPI()

# Test Database Configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Test Redis Configuration
TEST_REDIS_URL = "redis://localhost:6379/15"

class TestSettings:
    """Test environment settings"""
    database_url = SQLALCHEMY_DATABASE_URL
    redis_url = TEST_REDIS_URL
    secret_key = "test-secret-key-very-secure"
    openai_api_key = "test-openai-key"
    github_token = "test-github-token"
    oauth_github_client_id = "test-github-client-id"
    oauth_github_client_secret = "test-github-client-secret"
    oauth_google_client_id = "test-google-client-id"
    oauth_google_client_secret = "test-google-client-secret"
    environment = "test"
    debug = True

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_settings():
    """Test configuration settings"""
    return TestSettings()

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Clean up tables
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def override_get_db(db_session):
    """Override the get_db dependency"""
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis client for testing"""
    mock_redis_client = Mock()
    mock_redis_client.get.return_value = None
    mock_redis_client.set.return_value = True
    mock_redis_client.delete.return_value = 1
    mock_redis_client.exists.return_value = False
    mock_redis_client.incr.return_value = 1
    mock_redis_client.expire.return_value = True
    
    def _get_test_redis():
        return mock_redis_client
    
    app.dependency_overrides[get_redis] = _get_test_redis
    yield mock_redis_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def client(override_get_db, mock_redis):
    """FastAPI test client"""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="function")
def authenticated_client(client, test_user):
    """Client with authenticated user"""
    # Mock authentication
    with patch("auth.get_current_user") as mock_auth:
        mock_auth.return_value = test_user
        yield client

@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "is_admin": False,
        "is_active": True
    }
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def admin_user(db_session):
    """Create an admin user"""
    user_data = {
        "email": "admin@example.com",
        "username": "admin",
        "full_name": "Admin User",
        "is_admin": True,
        "is_active": True
    }
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_blog_post(db_session, test_user):
    """Create a test blog post"""
    post_data = {
        "title": "Test Blog Post",
        "slug": "test-blog-post",
        "content": "This is a test blog post content",
        "excerpt": "Test excerpt",
        "status": "published",
        "author_id": test_user.id,
        "meta_title": "Test Meta Title",
        "meta_description": "Test meta description"
    }
    post = BlogPost(**post_data)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)
    return post

@pytest.fixture(scope="function")
def test_project(db_session):
    """Create a test portfolio project"""
    project_data = {
        "title": "Test Project",
        "slug": "test-project",
        "description": "A test project description",
        "github_url": "https://github.com/test/test-project",
        "demo_url": "https://test-project.com",
        "technologies": ["Python", "FastAPI", "React"],
        "status": "completed",
        "featured": True,
        "view_count": 0
    }
    project = Project(**project_data)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project

@pytest.fixture(scope="function")
def mock_openai():
    """Mock OpenAI API responses"""
    with patch("openai.OpenAI") as mock_client:
        # Mock completion response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Mock AI response"
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 100
        
        mock_client.return_value.chat.completions.create.return_value = mock_response
        
        # Mock embedding response
        mock_embedding_response = Mock()
        mock_embedding_response.data = [Mock()]
        mock_embedding_response.data[0].embedding = [0.1] * 1536
        mock_client.return_value.embeddings.create.return_value = mock_embedding_response
        
        yield mock_client

@pytest.fixture(scope="function")
def mock_github():
    """Mock GitHub API responses"""
    with patch("requests.get") as mock_get:
        # Mock repository response
        mock_repo_response = Mock()
        mock_repo_response.json.return_value = {
            "name": "test-repo",
            "description": "Test repository",
            "html_url": "https://github.com/test/test-repo",
            "language": "Python",
            "stargazers_count": 10,
            "forks_count": 5,
            "topics": ["python", "api"]
        }
        mock_repo_response.status_code = 200
        
        # Mock user response
        mock_user_response = Mock()
        mock_user_response.json.return_value = {
            "login": "testuser",
            "name": "Test User",
            "bio": "Test bio",
            "public_repos": 10,
            "followers": 5,
            "following": 3
        }
        mock_user_response.status_code = 200
        
        mock_get.return_value = mock_repo_response
        yield mock_get

@pytest.fixture(scope="function")
def sample_webhook_payload():
    """Sample webhook payload for testing"""
    return {
        "action": "push",
        "repository": {
            "name": "test-repo",
            "full_name": "user/test-repo",
            "html_url": "https://github.com/user/test-repo"
        },
        "commits": [
            {
                "id": "abc123",
                "message": "Test commit",
                "author": {
                    "name": "Test User",
                    "email": "test@example.com"
                }
            }
        ]
    }

@pytest.fixture(scope="function")
def mock_email_service():
    """Mock email service for testing"""
    with patch("services.email_service.send_email") as mock_send:
        mock_send.return_value = True
        yield mock_send

# Test data factories
class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_user_data(**kwargs):
        """Create user data with defaults"""
        defaults = {
            "email": "user@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "is_admin": False,
            "is_active": True
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    def create_blog_post_data(**kwargs):
        """Create blog post data with defaults"""
        defaults = {
            "title": "Test Post",
            "slug": "test-post",
            "content": "Test content",
            "excerpt": "Test excerpt",
            "status": "published",
            "meta_title": "Test Meta",
            "meta_description": "Test meta description"
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    def create_project_data(**kwargs):
        """Create project data with defaults"""
        defaults = {
            "title": "Test Project",
            "slug": "test-project",
            "description": "Test description",
            "github_url": "https://github.com/test/repo",
            "technologies": ["Python", "FastAPI"],
            "status": "completed",
            "featured": False
        }
        defaults.update(kwargs)
        return defaults

# Performance testing utilities
@pytest.fixture(scope="function")
def performance_timer():
    """Timer for performance testing"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()

# Security testing utilities
@pytest.fixture(scope="function")
def security_headers():
    """Expected security headers for testing"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'"
    }

# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Clean up test files after each test"""
    yield
    # Clean up any test files created during testing
    test_files = ["test.db", "test.log"]
    for file in test_files:
        if os.path.exists(file):
            try:
                os.remove(file)
            except Exception:
                pass