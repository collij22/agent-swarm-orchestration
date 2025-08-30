"""
Database utilities for query optimization and performance monitoring
Specialized for SQLite with TaskManagerAPI requirements
"""

import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from contextlib import contextmanager
import json

from .models import Task, User, Category, AIProcessingLog, TaskStatus, AIProcessingStatus
from .database import get_db_session

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """Advanced query optimization for TaskManagerAPI"""
    
    @staticmethod
    def get_user_tasks_with_pagination(
        db: Session, 
        user_id: str, 
        page: int = 1, 
        page_size: int = 20,
        status: Optional[str] = None,
        category_id: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Task], int]:
        """
        Optimized paginated task retrieval with filtering and sorting
        Returns (tasks, total_count)
        """
        # Base query with eager loading
        query = db.query(Task).filter(Task.user_id == user_id)
        
        # Apply filters
        if status:
            query = query.filter(Task.status == status)
        if category_id:
            query = query.filter(Task.category_id == category_id)
        
        # Get total count before applying pagination
        total_count = query.count()
        
        # Apply sorting
        sort_column = getattr(Task, sort_by, Task.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (page - 1) * page_size
        tasks = query.offset(offset).limit(page_size).all()
        
        return tasks, total_count
    
    @staticmethod
    def get_task_statistics(db: Session, user_id: str) -> Dict[str, Any]:
        """Get comprehensive task statistics for a user"""
        
        # Use single query with aggregation for efficiency
        stats_query = db.query(
            func.count(Task.id).label('total_tasks'),
            func.sum(func.case([(Task.status == TaskStatus.TODO, 1)], else_=0)).label('todo_count'),
            func.sum(func.case([(Task.status == TaskStatus.IN_PROGRESS, 1)], else_=0)).label('in_progress_count'),
            func.sum(func.case([(Task.status == TaskStatus.DONE, 1)], else_=0)).label('done_count'),
            func.avg(Task.priority).label('avg_priority'),
            func.sum(func.case([(Task.ai_categorized == True, 1)], else_=0)).label('ai_categorized_count'),
            func.sum(func.case([(Task.ai_prioritized == True, 1)], else_=0)).label('ai_prioritized_count')
        ).filter(Task.user_id == user_id).first()
        
        # Category distribution query
        category_stats = db.query(
            Category.name,
            func.count(Task.id).label('task_count')
        ).join(Task, Task.category_id == Category.id, isouter=True)\
         .filter(Task.user_id == user_id)\
         .group_by(Category.name)\
         .all()
        
        return {
            'total_tasks': stats_query.total_tasks or 0,
            'todo_count': stats_query.todo_count or 0,
            'in_progress_count': stats_query.in_progress_count or 0,
            'done_count': stats_query.done_count or 0,
            'completion_rate': round((stats_query.done_count or 0) / max(stats_query.total_tasks or 1, 1) * 100, 2),
            'avg_priority': round(float(stats_query.avg_priority or 3), 2),
            'ai_categorized_count': stats_query.ai_categorized_count or 0,
            'ai_prioritized_count': stats_query.ai_prioritized_count or 0,
            'category_distribution': {stat.name: stat.task_count for stat in category_stats}
        }
    
    @staticmethod
    def get_tasks_for_ai_processing(db: Session, limit: int = 10) -> List[Task]:
        """Get tasks that need AI processing, optimized for background processing"""
        
        return db.query(Task)\
                .filter(
                    Task.ai_processing_status.in_([AIProcessingStatus.PENDING, AIProcessingStatus.FAILED]),
                    ~Task.ai_categorized | ~Task.ai_prioritized  # Tasks missing AI processing
                )\
                .order_by(Task.created_at.asc())\
                .limit(limit)\
                .all()
    
    @staticmethod
    def bulk_update_task_status(db: Session, task_ids: List[str], user_id: str, status: str) -> int:
        """Bulk update task status for multiple tasks"""
        
        updated_count = db.query(Task)\
                         .filter(Task.id.in_(task_ids), Task.user_id == user_id)\
                         .update({Task.status: status}, synchronize_session=False)
        
        db.commit()
        return updated_count
    
    @staticmethod
    def search_tasks(
        db: Session, 
        user_id: str, 
        search_term: str, 
        limit: int = 50
    ) -> List[Task]:
        """Full-text search across task titles and descriptions"""
        
        # SQLite FTS would be ideal, but for MVP we'll use LIKE queries
        search_pattern = f"%{search_term}%"
        
        return db.query(Task)\
                .filter(
                    Task.user_id == user_id,
                    (Task.title.ilike(search_pattern) | Task.description.ilike(search_pattern))
                )\
                .order_by(Task.updated_at.desc())\
                .limit(limit)\
                .all()

class PerformanceMonitor:
    """Database performance monitoring and optimization"""
    
    @staticmethod
    @contextmanager
    def query_timer(operation_name: str):
        """Context manager to time database operations"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = (time.time() - start_time) * 1000
            logger.info(f"Query '{operation_name}' took {duration:.2f}ms")
            
            # Log slow queries (>100ms)
            if duration > 100:
                logger.warning(f"Slow query detected: '{operation_name}' took {duration:.2f}ms")
    
    @staticmethod
    def analyze_query_performance(db: Session) -> Dict[str, Any]:
        """Analyze database query performance"""
        
        # SQLite specific performance queries
        performance_stats = {}
        
        try:
            # Get database size
            db_size = db.execute(text("PRAGMA page_count * PRAGMA page_size")).scalar()
            performance_stats['database_size_mb'] = round(db_size / (1024 * 1024), 2) if db_size else 0
            
            # Get cache hit ratio
            cache_stats = db.execute(text("PRAGMA cache_size")).scalar()
            performance_stats['cache_size'] = cache_stats
            
            # Get index usage (approximate)
            index_info = db.execute(text("PRAGMA index_list('tasks')")).fetchall()
            performance_stats['task_indexes'] = len(index_info)
            
            # Get WAL mode status
            journal_mode = db.execute(text("PRAGMA journal_mode")).scalar()
            performance_stats['journal_mode'] = journal_mode
            
            # Table row counts for monitoring
            performance_stats['table_counts'] = {
                'users': db.query(User).count(),
                'tasks': db.query(Task).count(),
                'categories': db.query(Category).count(),
                'ai_logs': db.query(AIProcessingLog).count()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing query performance: {e}")
            performance_stats['error'] = str(e)
        
        return performance_stats
    
    @staticmethod
    def optimize_database(db: Session) -> Dict[str, Any]:
        """Run database optimization commands"""
        
        optimization_results = {}
        
        try:
            # Run ANALYZE to update statistics
            start_time = time.time()
            db.execute(text("ANALYZE"))
            optimization_results['analyze_time_ms'] = round((time.time() - start_time) * 1000, 2)
            
            # Run PRAGMA optimize
            start_time = time.time()
            db.execute(text("PRAGMA optimize"))
            optimization_results['optimize_time_ms'] = round((time.time() - start_time) * 1000, 2)
            
            # Check if VACUUM is needed (if database is >10MB and has >30% free pages)
            page_count = db.execute(text("PRAGMA page_count")).scalar()
            freelist_count = db.execute(text("PRAGMA freelist_count")).scalar()
            
            if page_count and freelist_count:
                free_percentage = (freelist_count / page_count) * 100
                optimization_results['free_space_percentage'] = round(free_percentage, 2)
                
                if free_percentage > 30 and page_count > 2560:  # >10MB and >30% free
                    optimization_results['vacuum_recommended'] = True
                else:
                    optimization_results['vacuum_recommended'] = False
            
            optimization_results['status'] = 'success'
            
        except Exception as e:
            logger.error(f"Error during database optimization: {e}")
            optimization_results['status'] = 'error'
            optimization_results['error'] = str(e)
        
        return optimization_results

class DatabaseHealthChecker:
    """Database health monitoring and diagnostics"""
    
    @staticmethod
    def check_integrity(db: Session) -> Dict[str, Any]:
        """Check database integrity"""
        
        integrity_results = {}
        
        try:
            # PRAGMA integrity_check
            integrity_check = db.execute(text("PRAGMA integrity_check")).fetchall()
            integrity_results['integrity_check'] = [row[0] for row in integrity_check]
            integrity_results['is_healthy'] = integrity_check[0][0] == 'ok' if integrity_check else False
            
            # Check foreign key constraints
            fk_check = db.execute(text("PRAGMA foreign_key_check")).fetchall()
            integrity_results['foreign_key_violations'] = len(fk_check)
            integrity_results['fk_violations'] = [dict(row) for row in fk_check] if fk_check else []
            
        except Exception as e:
            logger.error(f"Error checking database integrity: {e}")
            integrity_results['error'] = str(e)
            integrity_results['is_healthy'] = False
        
        return integrity_results
    
    @staticmethod
    def get_connection_info(db: Session) -> Dict[str, Any]:
        """Get database connection information"""
        
        connection_info = {}
        
        try:
            # SQLite specific connection info
            connection_info['sqlite_version'] = db.execute(text("SELECT sqlite_version()")).scalar()
            connection_info['journal_mode'] = db.execute(text("PRAGMA journal_mode")).scalar()
            connection_info['synchronous'] = db.execute(text("PRAGMA synchronous")).scalar()
            connection_info['cache_size'] = db.execute(text("PRAGMA cache_size")).scalar()
            connection_info['foreign_keys'] = bool(db.execute(text("PRAGMA foreign_keys")).scalar())
            
        except Exception as e:
            logger.error(f"Error getting connection info: {e}")
            connection_info['error'] = str(e)
        
        return connection_info

# Utility functions for common operations
def get_or_create_category(db: Session, name: str, description: str = "", color: str = "#6B7280") -> Category:
    """Get existing category or create new one"""
    
    category = db.query(Category).filter(Category.name == name).first()
    
    if not category:
        category = Category(name=name, description=description, color=color)
        db.add(category)
        db.commit()
        db.refresh(category)
    
    return category

def cleanup_old_ai_logs(db: Session, days_to_keep: int = 30) -> int:
    """Clean up old AI processing logs"""
    
    cutoff_date = func.datetime('now', f'-{days_to_keep} days')
    
    deleted_count = db.query(AIProcessingLog)\
                     .filter(AIProcessingLog.created_at < cutoff_date)\
                     .delete()
    
    db.commit()
    return deleted_count