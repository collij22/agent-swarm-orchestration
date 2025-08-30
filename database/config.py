"""
Database Configuration and Connection Management
Handles SQLite connections, connection pooling, and database settings
"""

import sqlite3
import os
import logging
from contextlib import contextmanager
from typing import Generator, Optional
from pathlib import Path
import threading
from functools import wraps
import time

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration settings"""
    
    def __init__(self):
        self.db_path = os.getenv("DATABASE_PATH", "data/taskmanager.db")
        self.enable_foreign_keys = True
        self.enable_wal_mode = True  # Write-Ahead Logging for better concurrency
        self.connection_timeout = 30.0
        self.busy_timeout = 30000  # 30 seconds in milliseconds
        self.cache_size = -64000  # 64MB cache (negative = KB)
        self.synchronous = "NORMAL"  # NORMAL, FULL, or OFF
        self.journal_mode = "WAL"  # WAL, DELETE, TRUNCATE, PERSIST, MEMORY, OFF
        self.temp_store = "MEMORY"  # MEMORY, FILE, DEFAULT
        
        # Ensure database directory exists
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

class DatabaseManager:
    """Manages database connections and provides connection pooling"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._local = threading.local()
        self._connection_count = 0
        self._max_connections = 10
        self._lock = threading.Lock()
    
    def _configure_connection(self, conn: sqlite3.Connection) -> None:
        """Configure a database connection with optimal settings"""
        
        # Enable foreign key constraints
        if self.config.enable_foreign_keys:
            conn.execute("PRAGMA foreign_keys = ON")
        
        # Set busy timeout for handling concurrent access
        conn.execute(f"PRAGMA busy_timeout = {self.config.busy_timeout}")
        
        # Configure cache size for performance
        conn.execute(f"PRAGMA cache_size = {self.config.cache_size}")
        
        # Set synchronous mode
        conn.execute(f"PRAGMA synchronous = {self.config.synchronous}")
        
        # Set journal mode (WAL for better concurrency)
        conn.execute(f"PRAGMA journal_mode = {self.config.journal_mode}")
        
        # Set temp store to memory for performance
        conn.execute(f"PRAGMA temp_store = {self.config.temp_store}")
        
        # Enable query optimization
        conn.execute("PRAGMA optimize")
        
        # Set row factory for dict-like access
        conn.row_factory = sqlite3.Row
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection for the current thread"""
        
        # Check if we have a connection for this thread
        if hasattr(self._local, 'connection'):
            conn = self._local.connection
            try:
                # Test if connection is still valid
                conn.execute("SELECT 1")
                return conn
            except sqlite3.Error:
                # Connection is invalid, create a new one
                pass
        
        # Create new connection
        with self._lock:
            if self._connection_count >= self._max_connections:
                raise Exception("Maximum number of database connections exceeded")
            
            self._connection_count += 1
        
        try:
            conn = sqlite3.connect(
                self.config.db_path,
                timeout=self.config.connection_timeout,
                check_same_thread=False
            )
            self._configure_connection(conn)
            self._local.connection = conn
            
            logger.debug(f"Created new database connection (total: {self._connection_count})")
            return conn
            
        except Exception as e:
            with self._lock:
                self._connection_count -= 1
            raise e
    
    @contextmanager
    def get_session(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database sessions with automatic transaction handling"""
        
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction rolled back: {e}")
            raise
    
    @contextmanager
    def get_cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """Context manager for database cursors"""
        
        with self.get_session() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()
    
    def close_connection(self) -> None:
        """Close the current thread's database connection"""
        
        if hasattr(self._local, 'connection'):
            try:
                self._local.connection.close()
                delattr(self._local, 'connection')
                
                with self._lock:
                    self._connection_count -= 1
                
                logger.debug(f"Closed database connection (remaining: {self._connection_count})")
                
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
    
    def execute_script(self, script: str) -> None:
        """Execute a SQL script (for migrations)"""
        
        with self.get_session() as conn:
            conn.executescript(script)
    
    def vacuum(self) -> None:
        """Vacuum the database to reclaim space and optimize"""
        
        logger.info("Starting database vacuum operation")
        start_time = time.time()
        
        with self.get_session() as conn:
            conn.execute("VACUUM")
        
        duration = time.time() - start_time
        logger.info(f"Database vacuum completed in {duration:.2f} seconds")
    
    def analyze(self) -> None:
        """Update database statistics for query optimization"""
        
        logger.info("Analyzing database for query optimization")
        
        with self.get_session() as conn:
            conn.execute("ANALYZE")
    
    def get_database_info(self) -> dict:
        """Get database information and statistics"""
        
        with self.get_cursor() as cursor:
            # Get database size
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            
            db_size = page_count * page_size
            
            # Get table information
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get index information
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            
            return {
                'database_path': self.config.db_path,
                'database_size_bytes': db_size,
                'database_size_mb': round(db_size / 1024 / 1024, 2),
                'page_count': page_count,
                'page_size': page_size,
                'tables': tables,
                'indexes': indexes,
                'connection_count': self._connection_count,
                'journal_mode': self.config.journal_mode,
                'synchronous': self.config.synchronous
            }

# Global database manager instance
db_manager = DatabaseManager()

def database_required(func):
    """Decorator to ensure database connection is available"""
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlite3.Error as e:
            logger.error(f"Database error in {func.__name__}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise
    
    return wrapper

@contextmanager
def get_db_session():
    """Convenience function for getting database session"""
    with db_manager.get_session() as session:
        yield session

@contextmanager  
def get_db_cursor():
    """Convenience function for getting database cursor"""
    with db_manager.get_cursor() as cursor:
        yield cursor

def init_database():
    """Initialize database with migrations"""
    from .migrate import DatabaseMigrator
    
    logger.info("Initializing database...")
    migrator = DatabaseMigrator(db_manager.config.db_path)
    
    if migrator.migrate_up():
        logger.info("Database initialized successfully")
        
        # Run optimization
        db_manager.analyze()
        
        return True
    else:
        logger.error("Failed to initialize database")
        return False

def cleanup_database():
    """Cleanup database connections and resources"""
    logger.info("Cleaning up database connections")
    db_manager.close_connection()

# Health check functions
def check_database_health() -> dict:
    """Check database health and return status"""
    
    try:
        with get_db_cursor() as cursor:
            # Test basic connectivity
            cursor.execute("SELECT 1")
            
            # Check if core tables exist
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='table' AND name IN ('users', 'tasks', 'categories')
            """)
            table_count = cursor.fetchone()[0]
            
            # Get basic statistics
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tasks")
            task_count = cursor.fetchone()[0]
            
            return {
                'status': 'healthy',
                'core_tables_present': table_count == 3,
                'user_count': user_count,
                'task_count': task_count,
                'connection_active': True
            }
            
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'connection_active': False
        }