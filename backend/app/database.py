"""
Database connection and session management for TaskManagerAPI
SQLite configuration optimized for performance and reliability
"""

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import sqlite3
import os
from contextlib import contextmanager
from typing import Generator
import logging

from .models import Base, get_default_categories

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./taskmanager.db")
DATABASE_DIR = os.path.dirname(os.path.abspath("taskmanager.db"))

# Ensure database directory exists
os.makedirs(DATABASE_DIR, exist_ok=True)

# SQLite optimization settings
def configure_sqlite(dbapi_connection, connection_record):
    """Configure SQLite for optimal performance"""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys=ON")
        
        # Performance optimizations
        cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
        cursor.execute("PRAGMA synchronous=NORMAL")  # Balance between speed and safety
        cursor.execute("PRAGMA cache_size=10000")  # Increase cache size (10MB)
        cursor.execute("PRAGMA temp_store=MEMORY")  # Store temporary tables in memory
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped I/O
        
        # Query optimization
        cursor.execute("PRAGMA optimize")
        
        cursor.close()

# Create engine with SQLite optimizations
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # Allow multiple threads
        "timeout": 30,  # 30 second timeout for database locks
    },
    poolclass=StaticPool,  # Use static pool for SQLite
    echo=False,  # Set to True for SQL debugging
    future=True
)

# Configure SQLite settings on connection
event.listen(engine, "connect", configure_sqlite)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class DatabaseManager:
    """Database management utilities"""
    
    @staticmethod
    def create_database():
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            return False
    
    @staticmethod
    def init_default_data():
        """Initialize database with default data"""
        try:
            db = SessionLocal()
            
            # Check if categories already exist
            from .models import Category
            existing_categories = db.query(Category).count()
            
            if existing_categories == 0:
                # Add default categories
                default_categories = get_default_categories()
                for category in default_categories:
                    db.add(category)
                
                db.commit()
                logger.info(f"Added {len(default_categories)} default categories")
            
            db.close()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize default data: {e}")
            return False
    
    @staticmethod
    def vacuum_database():
        """Optimize database by running VACUUM"""
        try:
            with engine.connect() as connection:
                connection.execute("VACUUM")
                connection.execute("PRAGMA optimize")
            logger.info("Database optimization completed")
            return True
        except Exception as e:
            logger.error(f"Failed to optimize database: {e}")
            return False
    
    @staticmethod
    def get_database_stats():
        """Get database statistics"""
        try:
            db = SessionLocal()
            from .models import User, Task, Category, AIProcessingLog
            
            stats = {
                "users": db.query(User).count(),
                "tasks": db.query(Task).count(),
                "categories": db.query(Category).count(),
                "ai_logs": db.query(AIProcessingLog).count(),
                "database_size_mb": os.path.getsize("taskmanager.db") / (1024 * 1024) if os.path.exists("taskmanager.db") else 0
            }
            
            db.close()
            return stats
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}

# Dependency to get database session
def get_database() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI
    Provides automatic session management with proper cleanup
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# Context manager for database sessions
@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions
    Use when you need a database session outside of FastAPI dependency injection
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database transaction error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# Database health check
def check_database_health() -> dict:
    """Check database connectivity and performance"""
    try:
        start_time = time.time()
        
        with get_db_session() as db:
            # Simple query to test connectivity
            result = db.execute("SELECT 1").scalar()
            
        response_time = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
            "database_url": DATABASE_URL.replace(os.getenv("DB_PASSWORD", ""), "***") if "DB_PASSWORD" in os.environ else DATABASE_URL
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "database_url": DATABASE_URL
        }

# Initialize database on module import
def initialize_database():
    """Initialize database with tables and default data"""
    logger.info("Initializing database...")
    
    if not DatabaseManager.create_database():
        raise RuntimeError("Failed to create database tables")
    
    if not DatabaseManager.init_default_data():
        logger.warning("Failed to initialize default data")
    
    logger.info("Database initialization completed")

# Import time for health check
import time