# TaskManagerAPI Database Architecture

## Overview
The TaskManagerAPI uses a normalized SQLite database with strategic indexing and performance optimizations. The schema is designed to support CRUD operations, AI-powered categorization, priority scoring, and comprehensive audit trails.

## Database Schema

### Entity Relationship Diagram
```
Users (1) -----> (N) Tasks (N) -----> (1) Categories
  |                 |
  |                 v
  |              TaskHistory (N)
  |                 |
  v                 v
TaskHistory (N)  AIProcessingQueue (N)
```

### Core Tables

#### Users Table
- **Purpose**: User authentication and task ownership
- **Key Fields**: id (UUID), username, email, password_hash
- **Indexes**: username, email (for login queries)
- **Constraints**: Unique username/email, email format validation

#### Categories Table  
- **Purpose**: Task categorization system (AI + user-defined)
- **Key Fields**: id (UUID), name, description, color, is_system_generated
- **Features**: Supports both AI-generated and user-created categories
- **Constraints**: Unique category names, hex color format validation

#### Tasks Table (Core Entity)
- **Purpose**: Main task management entity with AI enhancements
- **Key Fields**: 
  - Basic: id, title, description, status, priority, due_date
  - AI: ai_category_confidence, ai_priority_score, ai_last_processed
  - Relationships: user_id (FK), category_id (FK)
- **Status Values**: 'todo', 'in_progress', 'done'
- **Priority Scale**: 1-5 (1=lowest, 5=highest)

#### TaskHistory Table
- **Purpose**: Audit trail for all task changes
- **Key Fields**: task_id (FK), user_id (FK), action, old_values, new_values
- **Features**: JSON storage for change tracking, automatic timestamp

#### AIProcessingQueue Table
- **Purpose**: Async AI processing management
- **Key Fields**: task_id (FK), processing_type, status, retry_count
- **Processing Types**: 'categorization', 'priority_scoring'
- **Status Values**: 'pending', 'processing', 'completed', 'failed'

## Indexing Strategy

### Primary Indexes (Performance Critical)
```sql
-- User-based queries (most common access pattern)
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX idx_tasks_user_created ON tasks(user_id, created_at DESC);

-- Category-based filtering
CREATE INDEX idx_tasks_category ON tasks(category_id);
CREATE INDEX idx_tasks_category_status ON tasks(category_id, status);

-- Priority and sorting
CREATE INDEX idx_tasks_priority ON tasks(priority DESC);
CREATE INDEX idx_tasks_due_date ON tasks(due_date ASC) WHERE due_date IS NOT NULL;
```

### Secondary Indexes (Feature Support)
```sql
-- AI processing optimization
CREATE INDEX idx_tasks_ai_processing ON tasks(ai_last_processed ASC) WHERE ai_last_processed IS NULL;
CREATE INDEX idx_ai_queue_status ON ai_processing_queue(status, created_at ASC);

-- Authentication and audit
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_task_history_task ON task_history(task_id, created_at DESC);
```

## Performance Optimizations

### SQLite Configuration
```sql
PRAGMA journal_mode=WAL;        -- Write-Ahead Logging for concurrency
PRAGMA synchronous=NORMAL;      -- Balance safety and performance  
PRAGMA cache_size=10000;        -- 10MB cache
PRAGMA temp_store=memory;       -- Memory temp tables
PRAGMA mmap_size=268435456;     -- 256MB memory-mapped I/O
```

### Query Optimization Patterns

#### 1. User Task Retrieval (Most Common)
```sql
-- Optimized with compound index (user_id, status)
SELECT t.*, c.name as category_name 
FROM tasks t 
LEFT JOIN categories c ON t.category_id = c.id 
WHERE t.user_id = ? AND t.status = ?
ORDER BY t.priority DESC, t.created_at DESC;
```

#### 2. Dashboard Statistics
```sql
-- Uses indexes for fast aggregation
SELECT status, COUNT(*) 
FROM tasks 
WHERE user_id = ? 
GROUP BY status;
```

#### 3. AI Processing Queue
```sql
-- Optimized for FIFO processing
SELECT * FROM ai_processing_queue 
WHERE status = 'pending' 
ORDER BY created_at ASC 
LIMIT 10;
```

## Data Integrity

### Foreign Key Constraints
- All foreign keys have ON DELETE CASCADE or SET NULL
- Foreign key constraints enabled via PRAGMA
- Referential integrity enforced at database level

### Business Logic Constraints
```sql
-- Priority range validation
CONSTRAINT chk_priority_range CHECK (priority >= 1 AND priority <= 5)

-- Status value validation  
CONSTRAINT chk_status_values CHECK (status IN ('todo', 'in_progress', 'done'))

-- AI confidence score validation
CONSTRAINT chk_ai_confidence CHECK (ai_category_confidence IS NULL OR 
    (ai_category_confidence >= 0.0 AND ai_category_confidence <= 1.0))
```

### Automatic Triggers
```sql
-- Timestamp updates
CREATE TRIGGER update_tasks_timestamp 
    AFTER UPDATE ON tasks
    FOR EACH ROW
BEGIN
    UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Audit trail logging
CREATE TRIGGER log_task_changes 
    AFTER UPDATE ON tasks
    FOR EACH ROW
BEGIN
    INSERT INTO task_history (task_id, user_id, action, old_values, new_values)
    VALUES (NEW.id, NEW.user_id, 'updated', 
            json_object('status', OLD.status, 'priority', OLD.priority),
            json_object('status', NEW.status, 'priority', NEW.priority));
END;
```

## Migration Strategy

### Version Control
- Sequential numbered migrations (001_initial_schema.py)
- Up/down migration support with rollback capability
- Migration tracking in schema_migrations table

### Safe Migration Practices
```python
# Example migration structure
class Migration001:
    def up(self):
        # Create tables, indexes, insert default data
        # Record migration in schema_migrations
        
    def down(self):
        # Drop in reverse dependency order
        # Remove migration record
```

## Performance Monitoring

### Query Analysis Tools
```python
# Explain query execution plan
EXPLAIN QUERY PLAN SELECT * FROM tasks WHERE user_id = ?;

# Index usage analysis
SELECT name, tbl_name FROM sqlite_master WHERE type = 'index';

# Table statistics
SELECT COUNT(*) FROM tasks;
```

### Health Check Metrics
- Database connection status
- Table row counts
- Database file size
- Query execution plans
- Index usage statistics

## Scaling Considerations

### Current Limitations (SQLite)
- Single writer (WAL mode improves but doesn't eliminate)
- File-based storage (good for MVP, limited for distributed)
- No built-in replication

### Future Migration Path
- UUID primary keys enable easy migration to PostgreSQL
- Normalized schema supports horizontal partitioning
- Clean separation allows microservice extraction

### Performance Thresholds
- **Tasks per user**: Optimized for 1K-10K tasks
- **Concurrent users**: 10-100 (SQLite limitation)
- **Database size**: Up to 1GB efficiently
- **Query response**: <100ms for indexed queries

## Best Practices

### Query Optimization
1. Always filter by user_id first (leverages primary index)
2. Use compound indexes for multi-column WHERE clauses
3. Limit result sets with LIMIT clause
4. Use EXPLAIN QUERY PLAN for complex queries

### Data Management
1. Soft delete for critical data (keep audit trail)
2. Regular cleanup of completed AI processing queue items
3. Archive old task history periodically
4. Monitor database size and performance metrics

### Development Guidelines
1. Use SQLAlchemy ORM for type safety and relationship management
2. Implement database migrations for schema changes
3. Test queries with realistic data volumes
4. Monitor slow query log in production

## API Integration

### FastAPI Dependencies
```python
from database.database import get_db

@app.get("/tasks")
async def get_tasks(db: Session = Depends(get_db)):
    return TaskQueries.get_user_tasks(db, user_id)
```

### Connection Management
- Connection pooling with SQLAlchemy
- Automatic session cleanup
- Transaction management with rollback support
- Health check endpoints for monitoring

## Testing Strategy

### Unit Tests
- Model validation and constraints
- Query optimization and performance
- Migration up/down functionality
- Trigger behavior verification

### Integration Tests  
- Full CRUD operations
- Complex query scenarios
- Concurrent access patterns
- Data integrity under load

This database architecture provides a solid foundation for the TaskManagerAPI MVP while maintaining flexibility for future scaling and feature additions.