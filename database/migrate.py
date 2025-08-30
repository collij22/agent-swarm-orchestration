#!/usr/bin/env python3
"""
Database Migration Runner for TaskManagerAPI
Handles forward migrations and rollbacks with safety checks
"""

import sqlite3
import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self, db_path: str = "data/taskmanager.db"):
        """Initialize migrator with database path"""
        self.db_path = db_path
        self.migrations_dir = Path(__file__).parent / "migrations"
        self.ensure_database_directory()
    
    def ensure_database_directory(self):
        """Ensure database directory exists"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper configuration"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migrations"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT version FROM schema_migrations ORDER BY applied_at"
                )
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            return []
    
    def get_available_migrations(self) -> List[Tuple[str, Path]]:
        """Get list of available migration files"""
        migrations = []
        if not self.migrations_dir.exists():
            return migrations
        
        for file_path in sorted(self.migrations_dir.glob("*.sql")):
            version = file_path.stem
            migrations.append((version, file_path))
        
        return migrations
    
    def apply_migration(self, version: str, file_path: Path) -> bool:
        """Apply a single migration"""
        logger.info(f"Applying migration: {version}")
        
        try:
            with open(file_path, 'r') as f:
                migration_sql = f.read()
            
            with self.get_connection() as conn:
                # Execute migration in transaction
                conn.executescript(migration_sql)
                logger.info(f"[OK] Migration {version} applied successfully")
                return True
                
        except Exception as e:
            logger.error(f"[X] Failed to apply migration {version}: {e}")
            return False
    
    def rollback_migration(self, version: str) -> bool:
        """Rollback a specific migration"""
        logger.info(f"Rolling back migration: {version}")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT rollback_sql FROM schema_migrations WHERE version = ?",
                    (version,)
                )
                row = cursor.fetchone()
                
                if not row:
                    logger.error(f"No rollback information found for {version}")
                    return False
                
                rollback_sql = row[0]
                if not rollback_sql:
                    logger.error(f"No rollback SQL available for {version}")
                    return False
                
                # Execute rollback
                conn.executescript(rollback_sql)
                logger.info(f"[OK] Migration {version} rolled back successfully")
                return True
                
        except Exception as e:
            logger.error(f"[X] Failed to rollback migration {version}: {e}")
            return False
    
    def migrate_up(self, target_version: Optional[str] = None) -> bool:
        """Apply all pending migrations or up to target version"""
        applied = self.get_applied_migrations()
        available = self.get_available_migrations()
        
        logger.info(f"Applied migrations: {applied}")
        logger.info(f"Available migrations: {[v for v, _ in available]}")
        
        success = True
        for version, file_path in available:
            if version in applied:
                continue
            
            if target_version and version > target_version:
                break
            
            if not self.apply_migration(version, file_path):
                success = False
                break
        
        return success
    
    def migrate_down(self, target_version: str) -> bool:
        """Rollback migrations down to target version"""
        applied = self.get_applied_migrations()
        
        # Find migrations to rollback (in reverse order)
        to_rollback = [v for v in reversed(applied) if v > target_version]
        
        if not to_rollback:
            logger.info("No migrations to rollback")
            return True
        
        success = True
        for version in to_rollback:
            if not self.rollback_migration(version):
                success = False
                break
        
        return success
    
    def get_migration_status(self) -> dict:
        """Get current migration status"""
        applied = self.get_applied_migrations()
        available = self.get_available_migrations()
        
        status = {
            'database_exists': os.path.exists(self.db_path),
            'applied_migrations': applied,
            'available_migrations': [v for v, _ in available],
            'pending_migrations': [v for v, _ in available if v not in applied],
            'database_path': self.db_path
        }
        
        return status
    
    def reset_database(self) -> bool:
        """Reset database by removing file and reapplying all migrations"""
        logger.warning("Resetting database - all data will be lost!")
        
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                logger.info("Database file removed")
            
            return self.migrate_up()
            
        except Exception as e:
            logger.error(f"Failed to reset database: {e}")
            return False

def main():
    """CLI interface for migration runner"""
    if len(sys.argv) < 2:
        print("Usage: python migrate.py <command> [options]")
        print("Commands:")
        print("  up [version]     - Apply migrations up to version (all if not specified)")
        print("  down <version>   - Rollback migrations down to version")
        print("  status          - Show migration status")
        print("  reset           - Reset database and reapply all migrations")
        sys.exit(1)
    
    migrator = DatabaseMigrator()
    command = sys.argv[1]
    
    if command == "up":
        target = sys.argv[2] if len(sys.argv) > 2 else None
        success = migrator.migrate_up(target)
        sys.exit(0 if success else 1)
    
    elif command == "down":
        if len(sys.argv) < 3:
            print("Error: down command requires target version")
            sys.exit(1)
        target = sys.argv[2]
        success = migrator.migrate_down(target)
        sys.exit(0 if success else 1)
    
    elif command == "status":
        status = migrator.get_migration_status()
        print(f"Database: {status['database_path']}")
        print(f"Exists: {status['database_exists']}")
        print(f"Applied: {status['applied_migrations']}")
        print(f"Available: {status['available_migrations']}")
        print(f"Pending: {status['pending_migrations']}")
    
    elif command == "reset":
        confirm = input("This will delete all data. Continue? (y/N): ")
        if confirm.lower() == 'y':
            success = migrator.reset_database()
            sys.exit(0 if success else 1)
        else:
            print("Reset cancelled")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()