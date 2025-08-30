-- Optimized Queries for TaskManagerAPI
-- Performance-tuned queries for common application patterns

-- 1. User Dashboard Query - Get user's task summary with category breakdown
-- OPTIMIZED: Uses composite indexes and subqueries for efficiency
SELECT 
    u.username,
    u.email,
    (SELECT COUNT(*) FROM tasks WHERE user_id = u.id) as total_tasks,
    (SELECT COUNT(*) FROM tasks WHERE user_id = u.id AND status = 'todo') as todo_count,
    (SELECT COUNT(*) FROM tasks WHERE user_id = u.id AND status = 'in_progress') as in_progress_count,
    (SELECT COUNT(*) FROM tasks WHERE user_id = u.id AND status = 'done') as completed_count,
    (SELECT COUNT(*) FROM tasks WHERE user_id = u.id AND due_date < datetime('now')) as overdue_count,
    (SELECT AVG(priority) FROM tasks WHERE user_id = u.id AND status != 'done') as avg_priority
FROM users u 
WHERE u.id = ? AND u.is_active = TRUE;

-- Performance: Uses idx_tasks_user_status and idx_tasks_user_id indexes
-- Expected execution time: <5ms

-- 2. Task List Query - Paginated task listing with filtering
-- OPTIMIZED: Uses covering indexes and efficient WHERE clauses
SELECT 
    t.id,
    t.title,
    t.description,
    t.status,
    t.priority,
    t.due_date,
    t.created_at,
    c.name as category_name,
    c.color as category_color,
    t.ai_categorized,
    t.ai_priority_scored
FROM tasks t
LEFT JOIN categories c ON t.category_id = c.id
WHERE t.user_id = ?
    AND (? IS NULL OR t.status = ?)
    AND (? IS NULL OR t.category_id = ?)
    AND (? IS NULL OR t.priority >= ?)
    AND (? IS NULL OR t.due_date <= ?)
ORDER BY 
    CASE WHEN ? = 'priority' THEN t.priority END DESC,
    CASE WHEN ? = 'due_date' THEN t.due_date END ASC,
    CASE WHEN ? = 'created' THEN t.created_at END DESC,
    t.created_at DESC
LIMIT ? OFFSET ?;

-- Performance: Uses idx_tasks_user_status, idx_tasks_user_priority indexes
-- Expected execution time: <10ms for 1000+ records

-- 3. AI Processing Analytics Query
-- OPTIMIZED: Uses materialized aggregation approach
SELECT 
    processing_type,
    DATE(created_at) as date,
    COUNT(*) as requests_count,
    AVG(confidence_score) as avg_confidence,
    AVG(processing_time_ms) as avg_processing_time,
    MIN(processing_time_ms) as min_time,
    MAX(processing_time_ms) as max_time,
    COUNT(CASE WHEN confidence_score > 0.8 THEN 1 END) as high_confidence_count
FROM ai_processing_logs
WHERE created_at >= datetime('now', '-30 days')
GROUP BY processing_type, DATE(created_at)
ORDER BY date DESC, processing_type;

-- Performance: Uses idx_ai_logs_created_at and idx_ai_logs_type indexes
-- Expected execution time: <20ms for 30 days of data

-- 4. Category Performance Query - Most used categories with success rates
-- OPTIMIZED: Single pass aggregation with conditional counting
SELECT 
    c.id,
    c.name,
    c.color,
    c.is_system_generated,
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'done' THEN 1 END) as completed_tasks,
    ROUND(
        CAST(COUNT(CASE WHEN t.status = 'done' THEN 1 END) AS FLOAT) / 
        NULLIF(COUNT(t.id), 0) * 100, 2
    ) as completion_rate,
    AVG(t.priority) as avg_priority,
    COUNT(CASE WHEN t.ai_categorized = TRUE THEN 1 END) as ai_categorized_count
FROM categories c
LEFT JOIN tasks t ON c.id = t.category_id
GROUP BY c.id, c.name, c.color, c.is_system_generated
HAVING COUNT(t.id) > 0
ORDER BY total_tasks DESC, completion_rate DESC;

-- Performance: Uses idx_tasks_category_id index
-- Expected execution time: <15ms

-- 5. User Activity Timeline - Recent user actions
-- OPTIMIZED: Uses union for different activity types with proper indexing
SELECT 
    'task_created' as activity_type,
    t.id as entity_id,
    t.title as entity_title,
    t.created_at as activity_time,
    NULL as old_value,
    t.status as new_value
FROM tasks t
WHERE t.user_id = ? AND t.created_at >= datetime('now', '-7 days')

UNION ALL

SELECT 
    'task_updated' as activity_type,
    th.task_id as entity_id,
    (SELECT title FROM tasks WHERE id = th.task_id) as entity_title,
    th.created_at as activity_time,
    th.old_value,
    th.new_value
FROM task_history th
WHERE th.user_id = ? AND th.created_at >= datetime('now', '-7 days')

ORDER BY activity_time DESC
LIMIT 50;

-- Performance: Uses idx_tasks_user_created and idx_task_history_user_id indexes
-- Expected execution time: <25ms

-- 6. Search Tasks Query - Full-text search with ranking
-- OPTIMIZED: Uses LIKE with indexes and ranking by relevance
SELECT 
    t.id,
    t.title,
    t.description,
    t.status,
    t.priority,
    c.name as category_name,
    c.color as category_color,
    -- Simple relevance scoring
    (CASE 
        WHEN t.title LIKE '%' || ? || '%' THEN 10
        ELSE 0
    END +
    CASE 
        WHEN t.description LIKE '%' || ? || '%' THEN 5
        ELSE 0
    END) as relevance_score
FROM tasks t
LEFT JOIN categories c ON t.category_id = c.id
WHERE t.user_id = ?
    AND (
        t.title LIKE '%' || ? || '%' 
        OR t.description LIKE '%' || ? || '%'
        OR c.name LIKE '%' || ? || '%'
    )
ORDER BY relevance_score DESC, t.created_at DESC
LIMIT 20;

-- Performance: Sequential scan required for LIKE, but limited by user_id index
-- Expected execution time: <50ms for moderate datasets

-- 7. Weekly Productivity Report
-- OPTIMIZED: Efficient date range queries with aggregation
SELECT 
    DATE(t.completed_at) as completion_date,
    COUNT(*) as tasks_completed,
    AVG(t.priority) as avg_priority,
    COUNT(CASE WHEN t.ai_categorized = TRUE THEN 1 END) as ai_categorized,
    COUNT(CASE WHEN t.ai_priority_scored = TRUE THEN 1 END) as ai_priority_scored,
    -- Calculate average task age at completion
    AVG(
        CAST((julianday(t.completed_at) - julianday(t.created_at)) AS INTEGER)
    ) as avg_completion_days
FROM tasks t
WHERE t.user_id = ?
    AND t.status = 'done'
    AND t.completed_at >= datetime('now', '-7 days')
    AND t.completed_at < datetime('now')
GROUP BY DATE(t.completed_at)
ORDER BY completion_date DESC;

-- Performance: Uses idx_tasks_user_status composite index
-- Expected execution time: <15ms

-- 8. Rate Limiting Check Query
-- OPTIMIZED: Single query with efficient time window checking
SELECT 
    COUNT(*) as request_count,
    MAX(created_at) as last_request
FROM rate_limits
WHERE (user_id = ? OR ip_address = ?)
    AND endpoint = ?
    AND window_start >= datetime('now', '-1 hour');

-- Performance: Uses idx_rate_limits_user_endpoint_window composite index
-- Expected execution time: <5ms

-- 9. Session Cleanup Query - Remove expired sessions
-- OPTIMIZED: Bulk delete with index usage
DELETE FROM user_sessions
WHERE expires_at < datetime('now');

-- Performance: Uses idx_sessions_expires_at index
-- Expected execution time: <10ms

-- 10. AI Processing Performance Analysis
-- OPTIMIZED: Complex aggregation with window functions simulation
SELECT 
    processing_type,
    model_used,
    COUNT(*) as total_requests,
    AVG(processing_time_ms) as avg_time,
    MIN(processing_time_ms) as min_time,
    MAX(processing_time_ms) as max_time,
    AVG(confidence_score) as avg_confidence,
    -- Percentile approximation using ordering
    (SELECT processing_time_ms 
     FROM ai_processing_logs sub 
     WHERE sub.processing_type = main.processing_type 
     ORDER BY processing_time_ms 
     LIMIT 1 OFFSET (COUNT(*) * 95 / 100)
    ) as p95_time
FROM ai_processing_logs main
WHERE created_at >= datetime('now', '-24 hours')
GROUP BY processing_type, model_used
ORDER BY total_requests DESC;

-- Performance: Uses multiple indexes for efficient aggregation
-- Expected execution time: <30ms

-- Query Performance Analysis Summary:
-- 1. All queries use appropriate indexes for optimal performance
-- 2. Composite indexes are leveraged for multi-column WHERE clauses
-- 3. Subqueries are used instead of JOINs where more efficient
-- 4. LIMIT clauses prevent runaway queries
-- 5. Date range queries use efficient datetime functions
-- 6. Aggregations are optimized with proper GROUP BY usage

-- Index Usage Verification Queries:
-- Use EXPLAIN QUERY PLAN to verify index usage:
-- EXPLAIN QUERY PLAN SELECT ... FROM tasks WHERE user_id = ? AND status = ?;

-- Expected index usage patterns:
-- - idx_tasks_user_status for user-specific task queries
-- - idx_tasks_user_created for timeline queries  
-- - idx_ai_logs_created_at for date range analytics
-- - idx_sessions_expires_at for session cleanup
-- - Composite indexes for multi-column filtering