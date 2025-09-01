"""
Test configuration and fixtures for QuickShop MVP backend tests.
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import get_db, Base
from app.core.config import get_settings


# Test database setup
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


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = Mock()
    settings.SECRET_KEY = "test-secret-key-12345"
    settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    settings.REFRESH_TOKEN_EXPIRE_DAYS = 7
    settings.DATABASE_URL = "sqlite:///./test.db"
    settings.REDIS_URL = "redis://localhost:6379"
    settings.STRIPE_SECRET_KEY = "sk_test_123"
    settings.SENDGRID_API_KEY = "SG.test123"
    settings.AWS_ACCESS_KEY_ID = "test-access-key"
    settings.AWS_SECRET_ACCESS_KEY = "test-secret-key"
    settings.AWS_S3_BUCKET = "test-bucket"
    settings.GOOGLE_ANALYTICS_PROPERTY_ID = "GA_TEST_123"
    return settings


@pytest.fixture
def mock_stripe():
    """Mock Stripe service for testing."""
    mock = AsyncMock()
    mock.create_payment_intent.return_value = {
        "id": "pi_test_123",
        "client_secret": "pi_test_123_secret_test",
        "status": "requires_payment_method"
    }
    mock.confirm_payment_intent.return_value = {
        "id": "pi_test_123",
        "status": "succeeded"
    }
    return mock


@pytest.fixture
def mock_sendgrid():
    """Mock SendGrid service for testing."""
    mock = AsyncMock()
    mock.send_email.return_value = {"status_code": 202}
    return mock


@pytest.fixture
def mock_s3():
    """Mock AWS S3 service for testing."""
    mock = AsyncMock()
    mock.upload_file.return_value = "https://test-bucket.s3.amazonaws.com/test-file.jpg"
    mock.delete_file.return_value = True
    return mock


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "is_admin": False
    }


@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return {
        "name": "Test Product",
        "description": "A test product description",
        "price": 29.99,
        "category": "Electronics",
        "stock_quantity": 100,
        "image_url": "https://example.com/product.jpg",
        "is_active": True
    }


@pytest.fixture
def sample_order_data():
    """Sample order data for testing."""
    return {
        "items": [
            {
                "product_id": 1,
                "quantity": 2,
                "price": 29.99
            }
        ],
        "shipping_address": {
            "street": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "zip_code": "12345",
            "country": "USA"
        },
        "payment_method_id": "pm_test_123"
    }


@pytest.fixture
def auth_headers():
    """Sample authentication headers for testing."""
    return {
        "Authorization": "Bearer test-jwt-token"
    }


@pytest.fixture
def admin_headers():
    """Sample admin authentication headers for testing."""
    return {
        "Authorization": "Bearer test-admin-jwt-token"
    }


class TestDataFactory:
    """Factory class for creating test data."""
    
    @staticmethod
    def create_user(**kwargs):
        """Create a test user with optional overrides."""
        default_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
            "is_admin": False
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_product(**kwargs):
        """Create a test product with optional overrides."""
        default_data = {
            "name": "Test Product",
            "description": "A test product description",
            "price": 29.99,
            "category": "Electronics",
            "stock_quantity": 100,
            "image_url": "https://example.com/product.jpg",
            "is_active": True
        }
        default_data.update(kwargs)
        return default_data


@pytest.fixture
def test_factory():
    """Provide test data factory."""
    return TestDataFactory