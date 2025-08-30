"""
Database Configuration with Performance Optimizations
Optimized for <200ms API response times
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import QueuePool
import redis.asyncio as redis
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://user:password@localhost:5432/devportfolio"
)

# Redis URL for caching
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Optimized database engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    # Connection pool settings for high performance
    poolclass=QueuePool,
    pool_size=20,  # Base pool size
    max_overflow=30,  # Additional connections when needed
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections every hour
    
    # Performance optimizations
    echo=False,  # Disable SQL logging in production
    future=True,
    connect_args={
        "server_settings": {
            "jit": "off",  # Disable JIT compilation for consistent performance
        },
        "command_timeout": 5,  # 5 second query timeout
        "prepared_statement_cache_size": 100,
    }
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Redis connection pool
redis_pool = None

async def get_redis():
    """Get Redis connection with connection pooling"""
    global redis_pool
    if redis_pool is None:
        redis_pool = redis.ConnectionPool.from_url(
            REDIS_URL,
            max_connections=20,
            retry_on_timeout=True,
            socket_timeout=5,
            socket_connect_timeout=5,
        )
    return redis.Redis(connection_pool=redis_pool)

# Database dependency
@asynccontextmanager
async def get_db():
    """Database session dependency with automatic cleanup"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Base model
Base = declarative_base()

async def init_db():
    """Initialize database with optimized settings"""
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
        
        # Create performance indexes
        await conn.execute(text("""
            -- Blog post indexes for fast queries
            CREATE INDEX IF NOT EXISTS idx_blog_posts_published_at 
            ON blog_posts(published_at DESC) WHERE status = 'published';
            
            CREATE INDEX IF NOT EXISTS idx_blog_posts_slug 
            ON blog_posts(slug) WHERE status = 'published';
            
            CREATE INDEX IF NOT EXISTS idx_blog_posts_tags 
            ON blog_posts USING GIN(tags);
            
            -- Portfolio project indexes
            CREATE INDEX IF NOT EXISTS idx_projects_featured 
            ON projects(created_at DESC) WHERE featured = true;
            
            CREATE INDEX IF NOT EXISTS idx_projects_technologies 
            ON projects USING GIN(technologies);
            
            -- Analytics indexes for fast aggregation
            CREATE INDEX IF NOT EXISTS idx_analytics_date_path 
            ON analytics(date, path);
            
            CREATE INDEX IF NOT EXISTS idx_analytics_date_desc 
            ON analytics(date DESC);
            
            -- Comment system indexes
            CREATE INDEX IF NOT EXISTS idx_comments_post_approved 
            ON comments(post_id, created_at DESC) WHERE approved = true;
        """))
        
    logger.info("Database initialized with performance optimizations")

async def close_db():
    """Close database connections"""
    await engine.dispose()
    if redis_pool:
        await redis_pool.disconnect()
    logger.info("Database connections closed")