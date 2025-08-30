-- TaskManagerAPI Database Schema
-- Database: SQLite
-- Version: 1.0.0

-- Enable foreign key constraints in SQLite
PRAGMA foreign_keys = ON;

-- Users table
CREATE TABLE users (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_username_length CHECK (length(username) >= 3 AND length(username) <= 50),
    CONSTRAINT chk_email_format CHECK (email LIKE '%@%.%')
);

-- Categories table
CREATE TABLE categories (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    color TEXT DEFAULT '#6B7280',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_category_name_length CHECK (length(name) >= 1 AND length(name) <= 50),
    CONSTRAINT chk_color_format CHECK (color GLOB '#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]')
);

-- Tasks table
CREATE TABLE tasks (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'todo',
    priority INTEGER DEFAULT 3,
    ai_processed BOOLEAN DEFAULT FALSE,
    user_id TEXT NOT NULL,
    category_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    CONSTRAINT chk_title_length CHECK (length(title) >= 1 AND length(title) <= 200),
    CONSTRAINT chk_status CHECK (status IN ('todo', 'in_progress', 'done')),
    CONSTRAINT chk_priority CHECK (priority >= 1 AND priority <= 5)
);

-- AI Processing Log table (for tracking AI operations)
CREATE TABLE ai_processing_log (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    task_id TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    request_data TEXT,
    response_data TEXT,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    CONSTRAINT chk_operation_type CHECK (operation_type IN ('categorization', 'prioritization'))
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_category_id ON tasks(category_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX idx_tasks_updated_at ON tasks(updated_at DESC);
CREATE INDEX idx_tasks_ai_processed ON tasks(ai_processed);

CREATE INDEX idx_categories_name ON categories(name);

CREATE INDEX idx_ai_log_task_id ON ai_processing_log(task_id);
CREATE INDEX idx_ai_log_created_at ON ai_processing_log(created_at DESC);

-- Triggers for updated_at timestamps
CREATE TRIGGER update_users_timestamp 
AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_tasks_timestamp 
AFTER UPDATE ON tasks
BEGIN
    UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_categories_timestamp 
AFTER UPDATE ON categories
BEGIN
    UPDATE categories SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Default categories seed data
INSERT INTO categories (id, name, description, color) VALUES 
    ('550e8400-e29b-41d4-a716-446655440001', 'Work', 'Work-related tasks', '#3B82F6'),
    ('550e8400-e29b-41d4-a716-446655440002', 'Personal', 'Personal tasks', '#10B981'),
    ('550e8400-e29b-41d4-a716-446655440003', 'Shopping', 'Shopping lists and errands', '#F59E0B'),
    ('550e8400-e29b-41d4-a716-446655440004', 'Health', 'Health and fitness tasks', '#EF4444'),
    ('550e8400-e29b-41d4-a716-446655440005', 'Learning', 'Education and skill development', '#8B5CF6'),
    ('550e8400-e29b-41d4-a716-446655440006', 'Home', 'Home maintenance and chores', '#EC4899'),
    ('550e8400-e29b-41d4-a716-446655440007', 'Finance', 'Financial tasks and planning', '#14B8A6'),
    ('550e8400-e29b-41d4-a716-446655440008', 'Other', 'Uncategorized tasks', '#6B7280');

-- Views for common queries
CREATE VIEW user_task_summary AS
SELECT 
    u.id as user_id,
    u.username,
    COUNT(t.id) as total_tasks,
    SUM(CASE WHEN t.status = 'todo' THEN 1 ELSE 0 END) as todo_count,
    SUM(CASE WHEN t.status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_count,
    SUM(CASE WHEN t.status = 'done' THEN 1 ELSE 0 END) as done_count,
    SUM(CASE WHEN t.ai_processed = 1 THEN 1 ELSE 0 END) as ai_processed_count
FROM users u
LEFT JOIN tasks t ON u.id = t.user_id
GROUP BY u.id, u.username;

CREATE VIEW category_usage AS
SELECT 
    c.id as category_id,
    c.name as category_name,
    c.color,
    COUNT(t.id) as task_count,
    AVG(t.priority) as avg_priority
FROM categories c
LEFT JOIN tasks t ON c.id = t.category_id
GROUP BY c.id, c.name, c.color;

-- Migration notes:
-- 1. Run this script to create initial schema
-- 2. Use Alembic for future migrations
-- 3. Always backup database before migrations
-- 4. Test migrations in development first

-- Performance considerations:
-- 1. SQLite uses dynamic typing, so TEXT for UUIDs is efficient
-- 2. Indexes on foreign keys improve JOIN performance
-- 3. Partial indexes could be added for frequently filtered queries
-- 4. Consider WAL mode for better concurrency: PRAGMA journal_mode=WAL;

-- Security notes:
-- 1. password_hash should use bcrypt or similar
-- 2. All user inputs must be parameterized (handled by ORM)
-- 3. Regular backups should be automated
-- 4. Consider encryption at rest for production