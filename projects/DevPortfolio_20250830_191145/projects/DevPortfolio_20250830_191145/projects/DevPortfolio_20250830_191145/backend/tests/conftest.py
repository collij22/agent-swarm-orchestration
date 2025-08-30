"""
Test configuration and fixtures for DevPortfolio API
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, AsyncMock
import os
import tempfile

# Import the main app and database
from main import app
from database import Base, get_db
from models import User, Project, BlogPost
from auth.jwt_handler import create_access_token


# Test database configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    TestSessionLocal = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def override_get_db(test_db):
    """Override database dependency"""
    async def _override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(override_get_db) -> Generator[TestClient, None, None]:
    """Create test client"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_openai():
    """Mock OpenAI client"""
    mock = Mock()
    mock.chat = Mock()
    mock.chat.completions = Mock()
    mock.chat.completions.create = AsyncMock()
    return mock


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=False)
    return mock


@pytest.fixture
def mock_github_api():
    """Mock GitHub API responses"""
    mock = AsyncMock()
    mock.get_user_repos = AsyncMock(return_value=[
        {
            "name": "test-repo",
            "description": "Test repository",
            "html_url": "https://github.com/user/test-repo",
            "language": "Python",
            "stargazers_count": 10,
            "forks_count": 5
        }
    ])
    return mock


@pytest.fixture
async def test_user(test_db):
    """Create test user"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "hashed_password": "hashed_password",
        "is_active": True,
        "is_admin": False
    }
    user = User(**user_data)
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def admin_user(test_db):
    """Create admin test user"""
    user_data = {
        "email": "admin@example.com",
        "username": "admin",
        "full_name": "Admin User",
        "hashed_password": "hashed_password",
        "is_active": True,
        "is_admin": True
    }
    user = User(**user_data)
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers"""
    access_token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_auth_headers(admin_user):
    """Create admin authentication headers"""
    access_token = create_access_token({"sub": str(admin_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def test_project(test_db, test_user):
    """Create test project"""
    project_data = {
        "title": "Test Project",
        "description": "A test project",
        "github_url": "https://github.com/user/test-project",
        "demo_url": "https://demo.example.com",
        "technologies": ["Python", "FastAPI"],
        "user_id": test_user.id
    }
    project = Project(**project_data)
    test_db.add(project)
    await test_db.commit()
    await test_db.refresh(project)
    return project


@pytest.fixture
async def test_blog_post(test_db, test_user):
    """Create test blog post"""
    post_data = {
        "title": "Test Blog Post",
        "content": "# Test Content\n\nThis is a test blog post.",
        "excerpt": "This is a test blog post.",
        "slug": "test-blog-post",
        "tags": ["test", "blog"],
        "is_published": True,
        "user_id": test_user.id
    }
    post = BlogPost(**post_data)
    test_db.add(post)
    await test_db.commit()
    await test_db.refresh(post)
    return post


@pytest.fixture
def temp_file():
    """Create temporary file for testing"""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    """Set up test environment variables"""
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("GITHUB_TOKEN", "test-github-token")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("ENVIRONMENT", "test")