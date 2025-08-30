"""
Optimized Database Connection and Session Management
Enhanced PostgreSQL configuration for high performance
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import QueuePool
from sqlalchemy import event
import os
import logging
from typing import AsyncGenerator
import time
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Performance-optimized database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://portfolio_user:portfolio_pass@localhost:5432/devportfolio_db"
)

# Optimized engine configuration for high performance
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
    
    # Connection Pool Optimization
    poolclass=QueuePool,
    pool_size=50,  # Increased from 20
    max_overflow=100,  # Allow burst capacity
    pool_pre_ping=True,
    pool_recycle=1800,  # 30 minutes (reduced from 1 hour)
    pool_timeout=30,
    
    # Connection optimization
    connect_args={
        "server_settings": {
            "application_name": "DevPortfolio_API",
            "jit": "off",  # Disable JIT for consistent performance
        },
        "command_timeout": 60,
        "statement_cache_size": 0,  # Disable statement caching for high-throughput
    },
    
    # Query optimization
    execution_options={
        "isolation_level": "READ_COMMITTED",
        "autocommit": False,
    },
)

# Optimized session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

# Connection monitoring
connection_metrics = {
    "total_connections": 0,
    "active_connections": 0,
    "avg_query_time": 0.0,
    "slow_queries": 0,
}

@event.listens_for(engine.sync_engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Monitor query execution time"""
    context._query_start_time = time.time()

@event.listens_for(engine.sync_engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Track query performance metrics"""
    total_time = time.time() - context._query_start_time
    
    # Update metrics
    connection_metrics["avg_query_time"] = (
        (connection_metrics["avg_query_time"] + total_time) / 2
    )
    
    # Log slow queries (>100ms)
    if total_time > 0.1:
        connection_metrics["slow_queries"] += 1
        logger.warning(f"Slow query detected: {total_time:.3f}s - {statement[:100]}")

@asynccontextmanager
async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Optimized database session with proper error handling and metrics
    """
    session = AsyncSessionLocal()
    connection_metrics["total_connections"] += 1
    connection_metrics["active_connections"] += 1
    
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        await session.close()
        connection_metrics["active_connections"] -= 1

async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database session
    """
    async with get_database_session() as session:
        yield session

class DatabaseOptimizer:
    """Database performance optimization utilities"""
    
    @staticmethod
    async def create_indexes():
        """Create performance-critical indexes"""
        index_queries = [
            # User indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username ON users(username);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active ON users(is_active);",
            
            # Project indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_status ON projects(status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_featured ON projects(is_featured);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_created ON projects(created_at DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_category ON projects(category);",
            
            # Blog post indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_blog_posts_slug ON blog_posts(slug);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_blog_posts_status ON blog_posts(status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_blog_posts_published ON blog_posts(published_at DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_blog_posts_author ON blog_posts(author_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_blog_posts_category ON blog_posts(category);",
            
            # Comment indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_comments_post ON comments(post_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_comments_status ON comments(status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_comments_parent ON comments(parent_id);",
            
            # Analytics indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_type ON analytics_events(event_type);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_timestamp ON analytics_events(timestamp DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_visitor ON analytics_events(visitor_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_page ON analytics_events(page_path);",
            
            # Contact message indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contact_status ON contact_messages(status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contact_created ON contact_messages(created_at DESC);",
            
            # Composite indexes for common queries
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_blog_posts_status_published ON blog_posts(status, published_at DESC) WHERE status = 'published';",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_status_featured ON projects(status, is_featured, sort_order) WHERE status = 'active';",
        ]
        
        async with engine.begin() as conn:
            for query in index_queries:
                try:
                    await conn.execute(query)
                    logger.info(f"Index created: {query.split('idx_')[1].split(' ')[0]}")
                except Exception as e:
                    logger.warning(f"Index creation failed: {e}")
    
    @staticmethod
    async def analyze_tables():
        """Update table statistics for query optimization"""
        analyze_queries = [
            "ANALYZE users;",
            "ANALYZE projects;",
            "ANALYZE blog_posts;",
            "ANALYZE comments;",
            "ANALYZE analytics_events;",
            "ANALYZE contact_messages;",
            "ANALYZE skills;",
            "ANALYZE experiences;",
        ]
        
        async with engine.begin() as conn:
            for query in analyze_queries:
                await conn.execute(query)
        
        logger.info("Table statistics updated")
    
    @staticmethod
    async def get_performance_metrics():
        """Get database performance metrics"""
        return {
            **connection_metrics,
            "pool_size": engine.pool.size(),
            "pool_checked_in": engine.pool.checkedin(),
            "pool_checked_out": engine.pool.checkedout(),
        }

async def init_optimized_database():
    """
    Initialize database with performance optimizations
    """
    try:
        # Create tables
        from models.models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Create indexes
        await DatabaseOptimizer.create_indexes()
        
        # Analyze tables
        await DatabaseOptimizer.analyze_tables()
        
        logger.info("Optimized database initialized successfully")
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        raise

async def health_check():
    """Enhanced database health check with performance metrics"""
    try:
        start_time = time.time()
        
        async with get_database_session() as session:
            result = await session.execute("SELECT 1")
            is_connected = result.scalar() == 1
        
        response_time = time.time() - start_time
        metrics = await DatabaseOptimizer.get_performance_metrics()
        
        return {
            "database": "healthy" if is_connected else "unhealthy",
            "response_time_ms": round(response_time * 1000, 2),
            "connection_url": DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "unknown",
            "performance_metrics": metrics,
            "status": "optimal" if response_time < 0.1 else "degraded" if response_time < 0.5 else "slow"
        }
    except Exception as e:
        return {
            "database": "error",
            "error": str(e),
            "performance_metrics": connection_metrics
        }