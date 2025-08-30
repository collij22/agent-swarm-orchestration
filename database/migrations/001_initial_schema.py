"""
Initial database schema migration for TaskManagerAPI
Creates all core tables with proper relationships and indexes
"""

import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Any

class Migration001:
    """Initial schema migration"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.version = "001"
        self.description = "Initial schema creation"
    
    def up(self) -> None:
        """Apply migration - create all tables and indexes"""
        conn = sqlite3.connect(self.db_path)
        try:
            # Read and execute schema
            with open('database/schema.sql', 'r') as f:
                schema_sql = f.read()
            
            # Execute schema creation
            conn.executescript(schema_sql)
            
            # Insert default categories
            self._insert_default_categories(conn)
            
            # Record migration
            self._record_migration(conn)
            
            conn.commit()
            print(f"Migration {self.version} applied successfully")
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Migration {self.version} failed: {str(e)}")
        finally:
            conn.close()
    
    def down(self) -> None:
        """Rollback migration - drop all tables"""
        conn = sqlite3.connect(self.db_path)
        try:
            # Drop tables in reverse dependency order
            tables_to_drop = [
                'ai_processing_queue',
                'task_history', 
                'tasks',
                'categories',
                'users',
                'schema_migrations'
            ]
            
            for table in tables_to_drop:
                conn.execute(f"DROP TABLE IF EXISTS {table}")
            
            conn.commit()
            print(f"Migration {self.version} rolled back successfully")
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Migration {self.version} rollback failed: {str(e)}")
        finally:
            conn.close()
    
    def _insert_default_categories(self, conn: sqlite3.Connection) -> None:
        """Insert default task categories"""
        default_categories = [
            {
                'id': str(uuid.uuid4()),
                'name': 'Work',
                'description': 'Work-related tasks and projects',
                'color': '#3B82F6',
                'is_system_generated': True
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Personal',
                'description': 'Personal tasks and activities',
                'color': '#10B981',
                'is_system_generated': True
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Shopping',
                'description': 'Shopping lists and purchases',
                'color': '#F59E0B',
                'is_system_generated': True
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Health',
                'description': 'Health and fitness related tasks',
                'color': '#EF4444',
                'is_system_generated': True
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Learning',
                'description': 'Educational and skill development tasks',
                'color': '#8B5CF6',
                'is_system_generated': True
            }
        ]
        
        for category in default_categories:
            conn.execute("""
                INSERT INTO categories (id, name, description, color, is_system_generated)
                VALUES (?, ?, ?, ?, ?)
            """, (
                category['id'],
                category['name'],
                category['description'],
                category['color'],
                category['is_system_generated']
            ))
    
    def _record_migration(self, conn: sqlite3.Connection) -> None:
        """Record migration in schema_migrations table"""
        # Create migrations table if it doesn't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Record this migration
        conn.execute("""
            INSERT INTO schema_migrations (version, description)
            VALUES (?, ?)
        """, (self.version, self.description))

def run_migration(db_path: str, direction: str = 'up') -> None:
    """Run the migration in specified direction"""
    migration = Migration001(db_path)
    
    if direction == 'up':
        migration.up()
    elif direction == 'down':
        migration.down()
    else:
        raise ValueError("Direction must be 'up' or 'down'")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python 001_initial_schema.py <db_path> [up|down]")
        sys.exit(1)
    
    db_path = sys.argv[1]
    direction = sys.argv[2] if len(sys.argv) > 2 else 'up'
    
    run_migration(db_path, direction)