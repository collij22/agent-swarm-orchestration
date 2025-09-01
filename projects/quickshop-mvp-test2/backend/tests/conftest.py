"""
Test configuration and fixtures for QuickShop MVP backend tests
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings

# Test database URL - using SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    """Create a test client with test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers(client):
    """Create authentication headers for testing protected endpoints."""
    # Create test user and get token
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    # Register user
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    
    # Login to get token
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(client):
    """Create admin authentication headers for testing admin endpoints."""
    admin_data = {
        "email": "admin@quickshop.com",
        "password": "adminpassword123",
        "full_name": "Admin User",
        "is_admin": True
    }
    
    # Register admin user
    response = client.post("/api/v1/auth/register", json=admin_data)
    assert response.status_code == 201
    
    # Login to get token
    login_data = {
        "username": admin_data["email"],
        "password": admin_data["password"]
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return {
        "name": "Test Product",
        "description": "A test product description",
        "price": 29.99,
        "category": "Electronics",
        "stock_quantity": 100,
        "image_url": "https://example.com/image.jpg"
    }

@pytest.fixture
def sample_products(client, admin_headers, sample_product_data):
    """Create sample products for testing."""
    products = []
    for i in range(3):
        product_data = sample_product_data.copy()
        product_data["name"] = f"Test Product {i+1}"
        product_data["price"] = 19.99 + (i * 10)
        
        response = client.post(
            "/api/v1/products/", 
            json=product_data,
            headers=admin_headers
        )
        assert response.status_code == 201
        products.append(response.json())
    
    return products