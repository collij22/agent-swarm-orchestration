-- TaskManagerAPI Optimized Queries
-- Performance-tuned SQL queries for common operations

-- =====================================================
-- USER QUERIES
-- =====================================================

-- Get user by username (for authentication)
-- Uses index: idx_users_username
SELECT id, username, email, password_hash, is_active, created_at
FROM users 
WHERE username = ? AND is_active = TRUE;

-- Get user by email (for authentication)
-- Uses index: idx_users_email  
SELECT id, username, email, password_hash, is_active, created_at
FROM users 
WHERE email = ? AND is_active = TRUE;

-- Create new user
INSERT INTO users (username, email, password_hash)
VALUES (?, ?, ?);

-- =====================================================
-- TASK QUERIES
-- =====================================================

-- Get all tasks for a user with pagination and filtering
-- Uses indexes: idx_tasks_user_status, idx_tasks_user_priority
SELECT 
    t.id,
    t.title,
    t.description,
    t.priority,
    t.status,
    t.created_at,
    t.updated_at,
    t.due_date,
    t.completed_at,
    c.name as category_name,
    c.color as category_color
FROM tasks t
LEFT JOIN categories c ON t.category_id = c.id
WHERE t.user_id = ?
    AND (? IS NULL OR t.status = ?)  -- Status filter
    AND (? IS NULL OR t.category_id = ?)  -- Category filter
    AND (? IS NULL OR t.priority >= ?)  -- Priority filter
ORDER BY 
    CASE WHEN ? = 'priority' THEN t.priority END DESC,
    CASE WHEN ? = 'created' THEN t.created_at END DESC,
    CASE WHEN ? = 'due_date' THEN t.due_date END ASC,
    t.created_at DESC
LIMIT ? OFFSET ?;

-- Count tasks for pagination
SELECT COUNT(*) as total
FROM tasks t
WHERE t.user_id = ?
    AND (? IS NULL OR t.status = ?)
    AND (? IS NULL OR t.category_id = ?)
    AND (? IS NULL OR t.priority >= ?);

-- Get single task with category info
-- Uses index: idx_tasks_user_id (with additional filter)
SELECT 
    t.id,
    t.title,
    t.description,
    t.priority,
    t.status,
    t.created_at,
    t.updated_at,
    t.due_date,
    t.completed_at,
    t.user_id,
    c.name as category_name,
    c.color as category_color,
    c.id as category_id
FROM tasks t
LEFT JOIN categories c ON t.category_id = c.id
WHERE t.id = ? AND t.user_id = ?;

-- Create new task
INSERT INTO tasks (title, description, category_id, priority, status, due_date, user_id)
VALUES (?, ?, ?, ?, ?, ?, ?);

-- Update task
UPDATE tasks 
SET title = ?, 
    description = ?, 
    category_id = ?, 
    priority = ?, 
    status = ?,
    due_date = ?
WHERE id = ? AND user_id = ?;

-- Delete task
DELETE FROM tasks WHERE id = ? AND user_id = ?;

-- Update task status only
UPDATE tasks 
SET status = ?
WHERE id = ? AND user_id = ?;

-- Get tasks due soon (next 7 days)
-- Uses index: idx_tasks_due_date
SELECT 
    t.id,
    t.title,
    t.due_date,
    t.priority,
    c.name as category_name
FROM tasks t
LEFT JOIN categories c ON t.category_id = c.id
WHERE t.user_id = ?
    AND t.status != 'done'
    AND t.due_date IS NOT NULL
    AND t.due_date BETWEEN datetime('now') AND datetime('now', '+7 days')
ORDER BY t.due_date ASC, t.priority DESC;

-- Get task statistics for dashboard
SELECT 
    COUNT(*) as total_tasks,
    COUNT(CASE WHEN status = 'todo' THEN 1 END) as todo_count,
    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress_count,
    COUNT(CASE WHEN status = 'done' THEN 1 END) as done_count,
    COUNT(CASE WHEN due_date IS NOT NULL AND due_date < datetime('now') AND status != 'done' THEN 1 END) as overdue_count,
    AVG(priority) as avg_priority
FROM tasks 
WHERE user_id = ?;

-- =====================================================
-- CATEGORY QUERIES
-- =====================================================

-- Get all categories
-- Uses index: idx_categories_name
SELECT id, name, description, color, is_system_generated
FROM categories
ORDER BY is_system_generated DESC, name ASC;

-- Get category with task count
SELECT 
    c.id,
    c.name,
    c.description,
    c.color,
    COUNT(t.id) as task_count
FROM categories c
LEFT JOIN tasks t ON c.id = t.category_id AND t.user_id = ?
GROUP BY c.id, c.name, c.description, c.color
ORDER BY task_count DESC, c.name ASC;

-- Create new category
INSERT INTO categories (name, description, color)
VALUES (?, ?, ?);

-- Find or create category by name (for AI categorization)
INSERT OR IGNORE INTO categories (name, description, color, is_system_generated)
VALUES (?, ?, ?, TRUE);

SELECT id FROM categories WHERE name = ?;

-- =====================================================
-- AI PROCESSING LOG QUERIES
-- =====================================================

-- Log AI processing result
INSERT INTO ai_processing_log (task_id, processing_type, input_data, output_data, confidence_score, processing_time_ms)
VALUES (?, ?, ?, ?, ?, ?);

-- Get recent AI processing history for a task
-- Uses index: idx_ai_log_task_id
SELECT 
    processing_type,
    output_data,
    confidence_score,
    processing_time_ms,
    created_at
FROM ai_processing_log
WHERE task_id = ?
ORDER BY created_at DESC
LIMIT 10;

-- Get AI processing statistics
SELECT 
    processing_type,
    COUNT(*) as total_processes,
    AVG(confidence_score) as avg_confidence,
    AVG(processing_time_ms) as avg_processing_time,
    MIN(created_at) as first_process,
    MAX(created_at) as last_process
FROM ai_processing_log
WHERE created_at >= datetime('now', '-30 days')
GROUP BY processing_type;

-- =====================================================
-- PERFORMANCE ANALYSIS QUERIES
-- =====================================================

-- Check index usage
EXPLAIN QUERY PLAN 
SELECT t.*, c.name as category_name
FROM tasks t
LEFT JOIN categories c ON t.category_id = c.id
WHERE t.user_id = ? AND t.status = ?
ORDER BY t.priority DESC;

-- Database size analysis
SELECT 
    name,
    COUNT(*) as row_count,
    SUM(LENGTH(COALESCE(title, '') || COALESCE(description, ''))) as content_size
FROM (
    SELECT 'users' as name, username as title, email as description FROM users
    UNION ALL
    SELECT 'tasks' as name, title, description FROM tasks
    UNION ALL
    SELECT 'categories' as name, name as title, description FROM categories
    UNION ALL
    SELECT 'ai_processing_log' as name, processing_type as title, input_data as description FROM ai_processing_log
) 
GROUP BY name;

-- Slow query identification (tasks taking longer than average)
SELECT 
    t.id,
    t.title,
    t.created_at,
    COUNT(a.id) as ai_processes,
    AVG(a.processing_time_ms) as avg_ai_time
FROM tasks t
LEFT JOIN ai_processing_log a ON t.id = a.task_id
GROUP BY t.id, t.title, t.created_at
HAVING AVG(a.processing_time_ms) > (
    SELECT AVG(processing_time_ms) * 1.5 FROM ai_processing_log
)
ORDER BY avg_ai_time DESC;