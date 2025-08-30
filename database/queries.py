"""
Optimized database queries for TaskManagerAPI
Pre-built queries for common operations with performance optimization
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.orm import Session, joinedload, selectinload
from datetime import datetime, timedelta

from .models import User, Category, Task, TaskHistory, AIProcessingQueue

class TaskQueries:
    """Optimized queries for task operations"""
    
    @staticmethod
    def get_user_tasks(
        db: Session, 
        user_id: str, 
        status: Optional[str] = None,
        category_id: Optional[str] = None,
        priority_min: Optional[int] = None,
        priority_max: Optional[int] = None,
        due_before: Optional[datetime] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[Task]:
        """
        Get user tasks with advanced filtering and sorting
        Optimized with proper indexing and eager loading
        """
        # Base query with eager loading to prevent N+1 queries
        query = db.query(Task).options(
            joinedload(Task.category),
            joinedload(Task.user)
        ).filter(Task.user_id == user_id)
        
        # Apply filters
        if status:
            query = query.filter(Task.status == status)
        
        if category_id:
            query = query.filter(Task.category_id == category_id)
        
        if priority_min is not None:
            query = query.filter(Task.priority >= priority_min)
        
        if priority_max is not None:
            query = query.filter(Task.priority <= priority_max)
        
        if due_before:
            query = query.filter(Task.due_date <= due_before)
        
        if search:
            # Full-text search on title and description
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Task.title.ilike(search_term),
                    Task.description.ilike(search_term)
                )
            )
        
        # Apply sorting
        sort_column = getattr(Task, sort_by, Task.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Apply pagination
        return query.offset(offset).limit(limit).all()
    
    @staticmethod
    def get_task_with_history(db: Session, task_id: str, user_id: str) -> Optional[Task]:
        """Get task with complete history for detailed view"""
        return db.query(Task).options(
            joinedload(Task.category),
            joinedload(Task.user),
            selectinload(Task.history).joinedload(TaskHistory.user)
        ).filter(
            and_(Task.id == task_id, Task.user_id == user_id)
        ).first()
    
    @staticmethod
    def get_tasks_by_priority(db: Session, user_id: str, limit: int = 10) -> List[Task]:
        """Get highest priority tasks for dashboard"""
        return db.query(Task).options(
            joinedload(Task.category)
        ).filter(
            and_(Task.user_id == user_id, Task.status != 'done')
        ).order_by(
            desc(Task.priority),
            asc(Task.due_date.nullslast()),
            desc(Task.created_at)
        ).limit(limit).all()
    
    @staticmethod
    def get_overdue_tasks(db: Session, user_id: str) -> List[Task]:
        """Get overdue tasks for user"""
        now = datetime.utcnow()
        return db.query(Task).options(
            joinedload(Task.category)
        ).filter(
            and_(
                Task.user_id == user_id,
                Task.status != 'done',
                Task.due_date < now
            )
        ).order_by(asc(Task.due_date)).all()
    
    @staticmethod
    def get_tasks_needing_ai_processing(
        db: Session, 
        processing_type: str,
        limit: int = 10
    ) -> List[Task]:
        """Get tasks that need AI processing (categorization or priority scoring)"""
        return db.query(Task).filter(
            Task.ai_last_processed.is_(None)
        ).order_by(asc(Task.created_at)).limit(limit).all()
    
    @staticmethod
    def get_task_statistics(db: Session, user_id: str) -> Dict[str, Any]:
        """Get comprehensive task statistics for user dashboard"""
        # Base query for user tasks
        base_query = db.query(Task).filter(Task.user_id == user_id)
        
        # Status counts
        status_counts = db.query(
            Task.status,
            func.count(Task.id).label('count')
        ).filter(Task.user_id == user_id).group_by(Task.status).all()
        
        # Priority distribution
        priority_counts = db.query(
            Task.priority,
            func.count(Task.id).label('count')
        ).filter(Task.user_id == user_id).group_by(Task.priority).all()
        
        # Category distribution
        category_counts = db.query(
            Category.name,
            func.count(Task.id).label('count')
        ).join(Task).filter(Task.user_id == user_id).group_by(Category.name).all()
        
        # Completion rate (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        completed_recently = base_query.filter(
            and_(
                Task.status == 'done',
                Task.completed_at >= thirty_days_ago
            )
        ).count()
        
        created_recently = base_query.filter(
            Task.created_at >= thirty_days_ago
        ).count()
        
        completion_rate = (completed_recently / created_recently * 100) if created_recently > 0 else 0
        
        # Overdue count
        overdue_count = base_query.filter(
            and_(
                Task.status != 'done',
                Task.due_date < datetime.utcnow()
            )
        ).count()
        
        return {
            "total_tasks": base_query.count(),
            "status_counts": {status: count for status, count in status_counts},
            "priority_counts": {f"priority_{priority}": count for priority, count in priority_counts},
            "category_counts": {category: count for category, count in category_counts},
            "completion_rate_30d": round(completion_rate, 2),
            "overdue_count": overdue_count,
            "completed_recently": completed_recently
        }

class CategoryQueries:
    """Optimized queries for category operations"""
    
    @staticmethod
    def get_categories_with_task_counts(db: Session) -> List[Dict[str, Any]]:
        """Get all categories with task counts"""
        return db.query(
            Category.id,
            Category.name,
            Category.description,
            Category.color,
            func.count(Task.id).label('task_count')
        ).outerjoin(Task).group_by(
            Category.id,
            Category.name,
            Category.description,
            Category.color
        ).all()
    
    @staticmethod
    def get_user_categories(db: Session, user_id: str) -> List[Dict[str, Any]]:
        """Get categories used by specific user with task counts"""
        return db.query(
            Category.id,
            Category.name,
            Category.description,
            Category.color,
            func.count(Task.id).label('task_count')
        ).join(Task).filter(
            Task.user_id == user_id
        ).group_by(
            Category.id,
            Category.name,
            Category.description,
            Category.color
        ).all()

class AIQueries:
    """Optimized queries for AI processing operations"""
    
    @staticmethod
    def get_pending_ai_tasks(
        db: Session,
        processing_type: Optional[str] = None,
        limit: int = 50
    ) -> List[AIProcessingQueue]:
        """Get pending AI processing tasks"""
        query = db.query(AIProcessingQueue).options(
            joinedload(AIProcessingQueue.task)
        ).filter(AIProcessingQueue.status == 'pending')
        
        if processing_type:
            query = query.filter(AIProcessingQueue.processing_type == processing_type)
        
        return query.order_by(asc(AIProcessingQueue.created_at)).limit(limit).all()
    
    @staticmethod
    def get_failed_ai_tasks(db: Session, max_retries: int = 3) -> List[AIProcessingQueue]:
        """Get failed AI tasks that can be retried"""
        return db.query(AIProcessingQueue).options(
            joinedload(AIProcessingQueue.task)
        ).filter(
            and_(
                AIProcessingQueue.status == 'failed',
                AIProcessingQueue.retry_count < max_retries
            )
        ).order_by(asc(AIProcessingQueue.created_at)).all()
    
    @staticmethod
    def get_ai_processing_stats(db: Session) -> Dict[str, Any]:
        """Get AI processing statistics"""
        # Processing status counts
        status_counts = db.query(
            AIProcessingQueue.status,
            func.count(AIProcessingQueue.id).label('count')
        ).group_by(AIProcessingQueue.status).all()
        
        # Processing type counts
        type_counts = db.query(
            AIProcessingQueue.processing_type,
            func.count(AIProcessingQueue.id).label('count')
        ).group_by(AIProcessingQueue.processing_type).all()
        
        # Average processing time for completed tasks
        avg_processing_time = db.query(
            func.avg(
                func.julianday(AIProcessingQueue.completed_at) - 
                func.julianday(AIProcessingQueue.started_at)
            ).label('avg_time_days')
        ).filter(AIProcessingQueue.status == 'completed').scalar()
        
        # Convert days to seconds
        avg_processing_seconds = (avg_processing_time * 24 * 60 * 60) if avg_processing_time else 0
        
        return {
            "status_counts": {status: count for status, count in status_counts},
            "type_counts": {ptype: count for ptype, count in type_counts},
            "avg_processing_time_seconds": round(avg_processing_seconds, 2),
            "total_processed": sum(count for _, count in status_counts)
        }

class PerformanceQueries:
    """Performance monitoring and optimization queries"""
    
    @staticmethod
    def get_slow_query_candidates(db: Session) -> List[Dict[str, Any]]:
        """Identify potentially slow queries by analyzing table sizes and joins"""
        # Get table sizes
        table_stats = []
        
        tables = ['users', 'categories', 'tasks', 'task_history', 'ai_processing_queue']
        for table in tables:
            try:
                count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                table_stats.append({"table": table, "row_count": count})
            except:
                table_stats.append({"table": table, "row_count": 0})
        
        return table_stats
    
    @staticmethod
    def get_index_usage_stats(db: Session) -> List[Dict[str, Any]]:
        """Get index usage statistics (SQLite specific)"""
        try:
            # Get all indexes
            indexes = db.execute(text("""
                SELECT name, tbl_name, sql 
                FROM sqlite_master 
                WHERE type = 'index' 
                AND name NOT LIKE 'sqlite_%'
            """)).fetchall()
            
            return [
                {
                    "index_name": idx[0],
                    "table_name": idx[1],
                    "definition": idx[2]
                }
                for idx in indexes
            ]
        except Exception as e:
            return [{"error": str(e)}]
    
    @staticmethod
    def analyze_query_performance(db: Session, query_sql: str) -> Dict[str, Any]:
        """Analyze query performance using EXPLAIN QUERY PLAN"""
        try:
            # Get query execution plan
            plan = db.execute(text(f"EXPLAIN QUERY PLAN {query_sql}")).fetchall()
            
            analysis = {
                "query": query_sql,
                "execution_plan": [
                    {
                        "id": row[0],
                        "parent": row[1], 
                        "detail": row[3]
                    }
                    for row in plan
                ],
                "recommendations": []
            }
            
            # Analyze for performance issues
            plan_text = " ".join([row[3] for row in plan])
            
            if "SCAN TABLE" in plan_text:
                analysis["recommendations"].append("Consider adding indexes to avoid table scans")
            
            if "TEMP B-TREE" in plan_text:
                analysis["recommendations"].append("Query requires temporary sorting - consider adding composite index")
            
            return analysis
            
        except Exception as e:
            return {"error": str(e), "query": query_sql}

# Batch operations for better performance
class BatchOperations:
    """Batch operations for improved performance"""
    
    @staticmethod
    def bulk_update_task_priorities(
        db: Session,
        task_updates: List[Dict[str, Any]]
    ) -> int:
        """Bulk update task priorities"""
        try:
            # Prepare bulk update
            stmt = text("""
                UPDATE tasks 
                SET priority = :priority, ai_priority_score = :ai_score, 
                    ai_last_processed = CURRENT_TIMESTAMP
                WHERE id = :task_id
            """)
            
            db.execute(stmt, task_updates)
            db.commit()
            return len(task_updates)
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def bulk_categorize_tasks(
        db: Session,
        task_updates: List[Dict[str, Any]]
    ) -> int:
        """Bulk update task categories"""
        try:
            stmt = text("""
                UPDATE tasks 
                SET category_id = :category_id, ai_category_confidence = :confidence,
                    ai_last_processed = CURRENT_TIMESTAMP
                WHERE id = :task_id
            """)
            
            db.execute(stmt, task_updates)
            db.commit()
            return len(task_updates)
            
        except Exception as e:
            db.rollback()
            raise e