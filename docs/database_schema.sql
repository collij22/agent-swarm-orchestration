-- TaskManagerAPI Database Schema
-- SQLite3 Compatible

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Users table
CREATE TABLE users (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories table
CREATE TABLE categories (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    color TEXT DEFAULT '#6B7280',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tasks table
CREATE TABLE tasks (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    title TEXT NOT NULL,
    description TEXT,
    category_id TEXT,
    priority INTEGER DEFAULT 3 CHECK (priority >= 1 AND priority <= 5),
    status TEXT DEFAULT 'todo' CHECK (status IN ('todo', 'in_progress', 'done')),
    user_id TEXT NOT NULL,
    ai_categorized BOOLEAN DEFAULT 0,
    ai_prioritized BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_category_id ON tasks(category_id);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- Triggers for updated_at
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

-- Default categories seed data
INSERT INTO categories (name, description, color) VALUES
    ('Work', 'Work-related tasks and projects', '#3B82F6'),
    ('Personal', 'Personal tasks and reminders', '#10B981'),
    ('Shopping', 'Shopping lists and purchases', '#F59E0B'),
    ('Health', 'Health and fitness related tasks', '#EF4444'),
    ('Learning', 'Educational and skill development', '#8B5CF6'),
    ('Finance', 'Financial tasks and budgeting', '#6366F1'),
    ('Home', 'Household chores and maintenance', '#EC4899'),
    ('Other', 'Uncategorized tasks', '#6B7280');

-- API rate limiting table (optional for persistent rate limiting)
CREATE TABLE rate_limits (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT,
    ip_address TEXT,
    endpoint TEXT NOT NULL,
    requests INTEGER DEFAULT 1,
    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_rate_limits_user_id ON rate_limits(user_id);
CREATE INDEX idx_rate_limits_ip ON rate_limits(ip_address);
CREATE INDEX idx_rate_limits_window ON rate_limits(window_start);

-- AI processing logs (for tracking and debugging)
CREATE TABLE ai_logs (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    task_id TEXT NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN ('categorize', 'prioritize')),
    input_text TEXT NOT NULL,
    result TEXT NOT NULL,
    confidence REAL,
    tokens_used INTEGER,
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE INDEX idx_ai_logs_task_id ON ai_logs(task_id);
CREATE INDEX idx_ai_logs_created_at ON ai_logs(created_at DESC);