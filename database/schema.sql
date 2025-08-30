-- TaskManagerAPI Database Schema
-- Designed for SQLite with PostgreSQL compatibility
-- Created: 2025-01-27

-- Enable foreign key constraints in SQLite
PRAGMA foreign_keys = ON;

-- Users table - Core authentication and user management
CREATE TABLE users (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))), -- UUID-like format for SQLite
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    last_login DATETIME NULL
);

-- Categories table - Task categorization system
CREATE TABLE categories (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    color VARCHAR(7) DEFAULT '#3B82F6', -- Hex color code
    is_system_generated BOOLEAN DEFAULT FALSE, -- Tracks AI-generated vs user-created
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tasks table - Core task management with AI enhancements
CREATE TABLE tasks (
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
    ai_categorized BOOLEAN DEFAULT FALSE, -- Tracks if category was AI-generated
    ai_priority_scored BOOLEAN DEFAULT FALSE, -- Tracks if priority was AI-scored
    ai_confidence_score REAL DEFAULT 0.0 CHECK (ai_confidence_score >= 0.0 AND ai_confidence_score <= 1.0)
);

-- Task history table - Audit trail for task changes
CREATE TABLE task_history (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL, -- 'created', 'updated', 'status_changed', 'deleted'
    field_name VARCHAR(100), -- Which field was changed
    old_value TEXT,
    new_value TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- AI processing logs - Track AI categorization and priority scoring
CREATE TABLE ai_processing_logs (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    processing_type VARCHAR(50) NOT NULL, -- 'categorization', 'priority_scoring'
    input_data TEXT NOT NULL, -- JSON of input sent to AI
    output_data TEXT NOT NULL, -- JSON of AI response
    confidence_score REAL DEFAULT 0.0,
    processing_time_ms INTEGER DEFAULT 0,
    model_used VARCHAR(100) DEFAULT 'gpt-3.5-turbo',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User sessions table - JWT token management
CREATE TABLE user_sessions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE, -- Hashed JWT token for revocation
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    ip_address VARCHAR(45) -- Supports both IPv4 and IPv6
);

-- Rate limiting table - Track API usage per user
CREATE TABLE rate_limits (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    ip_address VARCHAR(45),
    endpoint VARCHAR(255) NOT NULL,
    request_count INTEGER DEFAULT 1,
    window_start DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert default categories
INSERT INTO categories (name, description, color, is_system_generated) VALUES
('Work', 'Professional and work-related tasks', '#EF4444', TRUE),
('Personal', 'Personal life and self-care tasks', '#10B981', TRUE),
('Shopping', 'Shopping lists and purchases', '#F59E0B', TRUE),
('Health', 'Health, fitness, and medical tasks', '#8B5CF6', TRUE),
('Learning', 'Educational and skill development', '#3B82F6', TRUE),
('Finance', 'Financial planning and money management', '#059669', TRUE),
('Home', 'Household chores and maintenance', '#DC2626', TRUE),
('Social', 'Social events and relationship management', '#EC4899', TRUE);

-- Triggers for updating updated_at timestamps
CREATE TRIGGER update_users_timestamp 
    AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_categories_timestamp 
    AFTER UPDATE ON categories
BEGIN
    UPDATE categories SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_tasks_timestamp 
    AFTER UPDATE ON tasks
BEGIN
    UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger for task completion timestamp
CREATE TRIGGER set_task_completion_timestamp
    AFTER UPDATE ON tasks
    WHEN NEW.status = 'done' AND OLD.status != 'done'
BEGIN
    UPDATE tasks SET completed_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger for task history logging
CREATE TRIGGER log_task_changes
    AFTER UPDATE ON tasks
BEGIN
    INSERT INTO task_history (task_id, user_id, action, field_name, old_value, new_value)
    VALUES (NEW.id, NEW.user_id, 'updated', 'status', OLD.status, NEW.status)
    WHERE OLD.status != NEW.status;
END;