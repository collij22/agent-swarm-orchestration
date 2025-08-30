-- Migration: 002_create_indexes
-- Description: Create performance indexes and views
-- Created: 2025-01-27
-- Author: Database Architect

-- Insert migration metadata
INSERT OR IGNORE INTO schema_migrations (version, description, rollback_sql) VALUES (
    '002_create_indexes',
    'Create performance indexes and statistical views',
    '-- Rollback script for 002_create_indexes
    DROP VIEW IF EXISTS v_ai_processing_stats;
    DROP VIEW IF EXISTS v_category_usage_stats;
    DROP VIEW IF EXISTS v_task_performance_stats;
    DROP INDEX IF EXISTS idx_rate_limits_ip_endpoint_window;
    DROP INDEX IF EXISTS idx_rate_limits_user_endpoint_window;
    DROP INDEX IF EXISTS idx_rate_limits_window;
    DROP INDEX IF EXISTS idx_rate_limits_endpoint;
    DROP INDEX IF EXISTS idx_rate_limits_ip;
    DROP INDEX IF EXISTS idx_rate_limits_user_id;
    DROP INDEX IF EXISTS idx_sessions_last_used;
    DROP INDEX IF EXISTS idx_sessions_expires_at;
    DROP INDEX IF EXISTS idx_sessions_token_hash;
    DROP INDEX IF EXISTS idx_sessions_user_id;
    DROP INDEX IF EXISTS idx_ai_logs_confidence;
    DROP INDEX IF EXISTS idx_ai_logs_created_at;
    DROP INDEX IF EXISTS idx_ai_logs_type;
    DROP INDEX IF EXISTS idx_ai_logs_task_id;
    DROP INDEX IF EXISTS idx_task_history_action;
    DROP INDEX IF EXISTS idx_task_history_created_at;
    DROP INDEX IF EXISTS idx_task_history_user_id;
    DROP INDEX IF EXISTS idx_task_history_task_id;
    DROP INDEX IF EXISTS idx_categories_system_generated;
    DROP INDEX IF EXISTS idx_categories_name;
    DROP INDEX IF EXISTS idx_tasks_category_status;
    DROP INDEX IF EXISTS idx_tasks_status_priority;
    DROP INDEX IF EXISTS idx_tasks_user_created;
    DROP INDEX IF EXISTS idx_tasks_user_priority;
    DROP INDEX IF EXISTS idx_tasks_user_status;
    DROP INDEX IF EXISTS idx_tasks_due_date;
    DROP INDEX IF EXISTS idx_tasks_updated_at;
    DROP INDEX IF EXISTS idx_tasks_created_at;
    DROP INDEX IF EXISTS idx_tasks_priority;
    DROP INDEX IF EXISTS idx_tasks_status;
    DROP INDEX IF EXISTS idx_tasks_category_id;
    DROP INDEX IF EXISTS idx_tasks_user_id;
    DROP INDEX IF EXISTS idx_users_created_at;
    DROP INDEX IF EXISTS idx_users_active;
    DROP INDEX IF EXISTS idx_users_username;
    DROP INDEX IF EXISTS idx_users_email;
    DELETE FROM schema_migrations WHERE version = ''002_create_indexes'';'
);

BEGIN TRANSACTION;

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Tasks table indexes (most critical for performance)
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_category_id ON tasks(category_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_updated_at ON tasks(updated_at);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_user_priority ON tasks(user_id, priority DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_user_created ON tasks(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_status_priority ON tasks(status, priority DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_category_status ON tasks(category_id, status);

-- Categories table indexes
CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name);
CREATE INDEX IF NOT EXISTS idx_categories_system_generated ON categories(is_system_generated);

-- Task history indexes for audit queries
CREATE INDEX IF NOT EXISTS idx_task_history_task_id ON task_history(task_id);
CREATE INDEX IF NOT EXISTS idx_task_history_user_id ON task_history(user_id);
CREATE INDEX IF NOT EXISTS idx_task_history_created_at ON task_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_task_history_action ON task_history(action);

-- AI processing logs indexes
CREATE INDEX IF NOT EXISTS idx_ai_logs_task_id ON ai_processing_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_ai_logs_type ON ai_processing_logs(processing_type);
CREATE INDEX IF NOT EXISTS idx_ai_logs_created_at ON ai_processing_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_logs_confidence ON ai_processing_logs(confidence_score DESC);

-- User sessions indexes for authentication
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON user_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_last_used ON user_sessions(last_used_at DESC);

-- Rate limiting indexes
CREATE INDEX IF NOT EXISTS idx_rate_limits_user_id ON rate_limits(user_id);
CREATE INDEX IF NOT EXISTS idx_rate_limits_ip ON rate_limits(ip_address);
CREATE INDEX IF NOT EXISTS idx_rate_limits_endpoint ON rate_limits(endpoint);
CREATE INDEX IF NOT EXISTS idx_rate_limits_window ON rate_limits(window_start);

-- Composite index for rate limiting queries
CREATE INDEX IF NOT EXISTS idx_rate_limits_user_endpoint_window ON rate_limits(user_id, endpoint, window_start);
CREATE INDEX IF NOT EXISTS idx_rate_limits_ip_endpoint_window ON rate_limits(ip_address, endpoint, window_start);

-- Performance monitoring views
CREATE VIEW IF NOT EXISTS v_task_performance_stats AS
SELECT 
    u.username,
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'done' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN t.status = 'in_progress' THEN 1 END) as in_progress_tasks,
    COUNT(CASE WHEN t.status = 'todo' THEN 1 END) as todo_tasks,
    AVG(t.priority) as avg_priority,
    COUNT(CASE WHEN t.ai_categorized = TRUE THEN 1 END) as ai_categorized_count,
    COUNT(CASE WHEN t.ai_priority_scored = TRUE THEN 1 END) as ai_priority_scored_count
FROM users u
LEFT JOIN tasks t ON u.id = t.user_id
WHERE u.is_active = TRUE
GROUP BY u.id, u.username;

-- Category usage statistics view
CREATE VIEW IF NOT EXISTS v_category_usage_stats AS
SELECT 
    c.name,
    c.color,
    c.is_system_generated,
    COUNT(t.id) as task_count,
    COUNT(CASE WHEN t.status = 'done' THEN 1 END) as completed_count,
    AVG(t.priority) as avg_priority,
    MAX(t.created_at) as last_used
FROM categories c
LEFT JOIN tasks t ON c.id = t.category_id
GROUP BY c.id, c.name, c.color, c.is_system_generated;

-- AI processing efficiency view
CREATE VIEW IF NOT EXISTS v_ai_processing_stats AS
SELECT 
    processing_type,
    COUNT(*) as total_requests,
    AVG(confidence_score) as avg_confidence,
    AVG(processing_time_ms) as avg_processing_time,
    MIN(processing_time_ms) as min_processing_time,
    MAX(processing_time_ms) as max_processing_time,
    DATE(created_at) as processing_date
FROM ai_processing_logs
GROUP BY processing_type, DATE(created_at)
ORDER BY processing_date DESC;

COMMIT;