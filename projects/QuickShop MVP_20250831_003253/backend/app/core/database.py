from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import redis

from app.core.config import settings

# PostgreSQL setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

# Dependency to get DB session
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get Redis client
def get_redis():
    return redis_client

# Database initialization
def init_db():
    """Initialize database with tables"""
    Base.metadata.create_all(bind=engine)

# Test database connection
def test_db_connection():
    """Test database connectivity"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

# Test Redis connection
def test_redis_connection():
    """Test Redis connectivity"""
    try:
        redis_client.ping()
        return True
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return False