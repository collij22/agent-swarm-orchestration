"""
Database configuration and connection management for TaskManagerAPI
Handles SQLite connection, session management, and database initialization
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./taskmanager.db")
DATABASE_PATH = DATABASE_URL.replace("sqlite:///", "")

# SQLite-specific configurations
def _configure_sqlite_connection(dbapi_connection, connection_record):
    """Configure SQLite connection settings for optimal performance"""
    cursor = dbapi_connection.cursor()
    
    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys=ON")
    
    # Optimize SQLite performance settings
    cursor.execute("PRAGMA journal_mode=WAL")        # Write-Ahead Logging for better concurrency
    cursor.execute("PRAGMA synchronous=NORMAL")      # Balance between safety and performance
    cursor.execute("PRAGMA cache_size=10000")        # 10MB cache
    cursor.execute("PRAGMA temp_store=memory")       # Store temp tables in memory
    cursor.execute("PRAGMA mmap_size=268435456")     # 256MB memory-mapped I/O
    
    cursor.close()

# Create engine with SQLite optimizations
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # Allow multiple threads
        "timeout": 20,               # 20 second timeout for busy database
    },
    poolclass=StaticPool,            # Use static pool for SQLite
    echo=os.getenv("DEBUG", "false").lower() == "true"  # Log SQL queries in debug mode
)

# Configure SQLite connection
event.listen(engine, "connect", _configure_sqlite_connection)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class DatabaseManager:
    """Database manager for handling connections and operations"""
    
    def __init__(self, database_url: str = DATABASE_URL):
        self.database_url = database_url
        self.engine = engine
    
    def create_database(self) -> None:
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            print("Database tables created successfully")
        except Exception as e:
            print(f"Error creating database tables: {e}")
            raise
    
    def drop_database(self) -> None:
        """Drop all database tables"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            print("Database tables dropped successfully")
        except Exception as e:
            print(f"Error dropping database tables: {e}")
            raise
    
    def reset_database(self) -> None:
        """Reset database by dropping and recreating all tables"""
        self.drop_database()
        self.create_database()
    
    def check_connection(self) -> bool:
        """Check if database connection is working"""
        try:
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def get_database_stats(self) -> dict:
        """Get database statistics and health information"""
        try:
            with self.engine.connect() as connection:
                # Get table counts
                tables = ['users', 'categories', 'tasks', 'task_history', 'ai_processing_queue']
                stats = {}
                
                for table in tables:
                    try:
                        result = connection.execute(f"SELECT COUNT(*) FROM {table}")
                        stats[f"{table}_count"] = result.scalar()
                    except:
                        stats[f"{table}_count"] = 0
                
                # Get database size
                if os.path.exists(DATABASE_PATH):
                    stats["database_size_mb"] = round(os.path.getsize(DATABASE_PATH) / 1024 / 1024, 2)
                else:
                    stats["database_size_mb"] = 0
                
                # Get SQLite version
                result = connection.execute("SELECT sqlite_version()")
                stats["sqlite_version"] = result.scalar()
                
                return stats
        except Exception as e:
            print(f"Error getting database stats: {e}")
            return {"error": str(e)}

# Database dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """
    Database dependency for FastAPI endpoints
    Provides database session with automatic cleanup
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions
    Use this for operations outside of FastAPI endpoints
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

# Database initialization functions
def init_database() -> None:
    """Initialize database with tables and default data"""
    db_manager = DatabaseManager()
    
    # Create tables
    db_manager.create_database()
    
    # Run initial migration if needed
    if not os.path.exists(DATABASE_PATH) or os.path.getsize(DATABASE_PATH) == 0:
        print("Running initial database migration...")
        try:
            from .migrations.migration_001_initial_schema import run_migration
            run_migration(DATABASE_PATH, 'up')
        except ImportError:
            print("Migration script not found, using SQLAlchemy table creation")
    
    print("Database initialized successfully")

def ensure_database_exists() -> None:
    """Ensure database exists and is properly configured"""
    if not os.path.exists(DATABASE_PATH):
        print(f"Database not found at {DATABASE_PATH}, creating new database...")
        init_database()
    else:
        # Verify database connection
        db_manager = DatabaseManager()
        if not db_manager.check_connection():
            print("Database connection failed, attempting to recreate...")
            init_database()

# Health check function
def health_check() -> dict:
    """Perform database health check"""
    db_manager = DatabaseManager()
    
    health_status = {
        "database": "unknown",
        "connection": False,
        "stats": {}
    }
    
    try:
        # Check connection
        health_status["connection"] = db_manager.check_connection()
        
        if health_status["connection"]:
            health_status["database"] = "healthy"
            health_status["stats"] = db_manager.get_database_stats()
        else:
            health_status["database"] = "unhealthy"
    
    except Exception as e:
        health_status["database"] = "error"
        health_status["error"] = str(e)
    
    return health_status

# Query optimization utilities
class QueryOptimizer:
    """Utilities for query optimization and performance monitoring"""
    
    @staticmethod
    def explain_query(db_session: Session, query) -> list:
        """Get query execution plan for optimization"""
        try:
            # Convert SQLAlchemy query to raw SQL
            sql = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
            
            # Get query plan
            result = db_session.execute(f"EXPLAIN QUERY PLAN {sql}")
            return [dict(row) for row in result]
        except Exception as e:
            return [{"error": str(e)}]
    
    @staticmethod
    def analyze_slow_queries(db_session: Session) -> dict:
        """Analyze database for potential performance issues"""
        analysis = {
            "table_scans": [],
            "missing_indexes": [],
            "recommendations": []
        }
        
        try:
            # Check for tables without indexes on foreign keys
            tables_info = db_session.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """).fetchall()
            
            for table in tables_info:
                table_name = table[0]
                
                # Get table info
                table_info = db_session.execute(f"PRAGMA table_info({table_name})").fetchall()
                indexes = db_session.execute(f"PRAGMA index_list({table_name})").fetchall()
                
                # Analyze for optimization opportunities
                fk_columns = [col[1] for col in table_info if col[1].endswith('_id')]
                indexed_columns = []
                
                for index in indexes:
                    index_info = db_session.execute(f"PRAGMA index_info({index[1]})").fetchall()
                    indexed_columns.extend([col[2] for col in index_info])
                
                # Find foreign keys without indexes
                unindexed_fks = [col for col in fk_columns if col not in indexed_columns]
                if unindexed_fks:
                    analysis["missing_indexes"].append({
                        "table": table_name,
                        "columns": unindexed_fks
                    })
        
        except Exception as e:
            analysis["error"] = str(e)
        
        return analysis

# Export main components
__all__ = [
    'engine',
    'SessionLocal', 
    'get_db',
    'get_db_session',
    'DatabaseManager',
    'init_database',
    'ensure_database_exists',
    'health_check',
    'QueryOptimizer'
]