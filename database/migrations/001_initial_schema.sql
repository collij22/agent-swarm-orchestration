-- Migration: 001_initial_schema
-- Description: Create initial database schema for TaskManagerAPI
-- Created: 2025-01-27
-- Author: Database Architect

-- Migration metadata
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    rollback_sql TEXT
);

-- Check if migration already applied
INSERT OR IGNORE INTO schema_migrations (version, description, rollback_sql) VALUES (
    '001_initial_schema',
    'Create initial database schema for TaskManagerAPI',
    '-- Rollback script for 001_initial_schema
    DROP TRIGGER IF EXISTS log_task_changes;
    DROP TRIGGER IF EXISTS set_task_completion_timestamp;
    DROP TRIGGER IF EXISTS update_tasks_timestamp;
    DROP TRIGGER IF EXISTS update_categories_timestamp;
    DROP TRIGGER IF EXISTS update_users_timestamp;
    DROP VIEW IF EXISTS v_ai_processing_stats;
    DROP VIEW IF EXISTS v_category_usage_stats;
    DROP VIEW IF EXISTS v_task_performance_stats;
    DROP TABLE IF EXISTS rate_limits;
    DROP TABLE IF EXISTS user_sessions;
    DROP TABLE IF EXISTS ai_processing_logs;
    DROP TABLE IF EXISTS task_history;
    DROP TABLE IF EXISTS tasks;
    DROP TABLE IF EXISTS categories;
    DROP TABLE IF EXISTS users;
    DELETE FROM schema_migrations WHERE version = ''001_initial_schema'';'
);

-- Proceed only if this migration hasn't been applied
BEGIN TRANSACTION;

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Create all tables (from schema.sql)
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    last_login DATETIME NULL
);

CREATE TABLE IF NOT EXISTS categories (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    color VARCHAR(7) DEFAULT '#3B82F6',
    is_system_generated BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category_id TEXT REFERENCES categories(id) ON DELETE SET NULL,
    priority INTEGER DEFAULT 3 CHECK (priority >= 1 AND priority <= 5),
    status VARCHAR(20) DEFAULT 'todo' CHECK (status IN ('todo', 'in_progress', 'done')),
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    due_date DATETIME NULL,
    completed_at DATETIME NULL,
    ai_categorized BOOLEAN DEFAULT FALSE,
    ai_priority_scored BOOLEAN DEFAULT FALSE,
    ai_confidence_score REAL DEFAULT 0.0 CHECK (ai_confidence_score >= 0.0 AND ai_confidence_score <= 1.0)
);

CREATE TABLE IF NOT EXISTS task_history (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_processing_logs (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    processing_type VARCHAR(50) NOT NULL,
    input_data TEXT NOT NULL,
    output_data TEXT NOT NULL,
    confidence_score REAL DEFAULT 0.0,
    processing_time_ms INTEGER DEFAULT 0,
    model_used VARCHAR(100) DEFAULT 'gpt-3.5-turbo',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_sessions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    ip_address VARCHAR(45)
);

CREATE TABLE IF NOT EXISTS rate_limits (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    ip_address VARCHAR(45),
    endpoint VARCHAR(255) NOT NULL,
    request_count INTEGER DEFAULT 1,
    window_start DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert default categories
INSERT OR IGNORE INTO categories (name, description, color, is_system_generated) VALUES
('Work', 'Professional and work-related tasks', '#EF4444', TRUE),
('Personal', 'Personal life and self-care tasks', '#10B981', TRUE),
('Shopping', 'Shopping lists and purchases', '#F59E0B', TRUE),
('Health', 'Health, fitness, and medical tasks', '#8B5CF6', TRUE),
('Learning', 'Educational and skill development', '#3B82F6', TRUE),
('Finance', 'Financial planning and money management', '#059669', TRUE),
('Home', 'Household chores and maintenance', '#DC2626', TRUE),
('Social', 'Social events and relationship management', '#EC4899', TRUE);

-- Create triggers
CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
    AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_categories_timestamp 
    AFTER UPDATE ON categories
BEGIN
    UPDATE categories SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_tasks_timestamp 
    AFTER UPDATE ON tasks
BEGIN
    UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS set_task_completion_timestamp
    AFTER UPDATE ON tasks
    WHEN NEW.status = 'done' AND OLD.status != 'done'
BEGIN
    UPDATE tasks SET completed_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS log_task_changes
    AFTER UPDATE ON tasks
BEGIN
    INSERT INTO task_history (task_id, user_id, action, field_name, old_value, new_value)
    VALUES (NEW.id, NEW.user_id, 'updated', 'status', OLD.status, NEW.status)
    WHERE OLD.status != NEW.status;
END;

COMMIT;