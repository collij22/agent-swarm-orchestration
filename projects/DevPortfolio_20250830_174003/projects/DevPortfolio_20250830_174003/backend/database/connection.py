"""
Database Connection and Session Management
PostgreSQL with SQLAlchemy async support
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
import logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://portfolio_user:portfolio_pass@localhost:5432/devportfolio_db"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()

async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

async def init_database():
    """
    Initialize database tables
    """
    from models.models import Base
    
    try:
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

async def check_database_connection():
    """
    Check if database connection is working
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute("SELECT 1")
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False

class DatabaseManager:
    """Database management utilities"""
    
    @staticmethod
    async def create_tables():
        """Create all database tables"""
        await init_database()
    
    @staticmethod
    async def drop_tables():
        """Drop all database tables (use with caution!)"""
        from models.models import Base
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("All database tables dropped")
    
    @staticmethod
    async def reset_database():
        """Reset database (drop and recreate tables)"""
        await DatabaseManager.drop_tables()
        await DatabaseManager.create_tables()
        logger.info("Database reset completed")

# Connection health check
async def health_check():
    """Database health check for monitoring"""
    try:
        is_connected = await check_database_connection()
        return {
            "database": "healthy" if is_connected else "unhealthy",
            "connection_url": DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "unknown"
        }
    except Exception as e:
        return {
            "database": "error",
            "error": str(e)
        }