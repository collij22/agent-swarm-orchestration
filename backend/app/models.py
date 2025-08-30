"""
Database models for TaskManagerAPI using SQLAlchemy ORM
Optimized for SQLite with proper relationships and constraints
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Optional, List
from enum import Enum

Base = declarative_base()

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress" 
    DONE = "done"

class AIProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class AIProcessingType(str, Enum):
    CATEGORIZATION = "categorization"
    PRIORITIZATION = "prioritization"

class AILogStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"

def generate_uuid():
    """Generate UUID as string for SQLite compatibility"""
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    color = Column(String(7), default="#3B82F6")  # Hex color code
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    tasks = relationship("Task", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name})>"

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    priority = Column(Integer, default=3)  # 1-5 scale
    status = Column(String(20), default=TaskStatus.TODO)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)
    
    # Foreign keys
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(String, ForeignKey("categories.id", ondelete="SET NULL"), index=True)
    
    # AI processing tracking
    ai_categorized = Column(Boolean, default=False)
    ai_prioritized = Column(Boolean, default=False)
    ai_processing_status = Column(String(20), default=AIProcessingStatus.PENDING, index=True)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    category = relationship("Category", back_populates="tasks")
    ai_logs = relationship("AIProcessingLog", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"
    
    @property
    def is_ai_processing(self) -> bool:
        """Check if task is currently being processed by AI"""
        return self.ai_processing_status == AIProcessingStatus.PROCESSING
    
    @property
    def needs_ai_processing(self) -> bool:
        """Check if task needs AI processing"""
        return (not self.ai_categorized or not self.ai_prioritized) and \
               self.ai_processing_status in [AIProcessingStatus.PENDING, AIProcessingStatus.FAILED]

class AIProcessingLog(Base):
    __tablename__ = "ai_processing_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    processing_type = Column(String(20), nullable=False)  # categorization or prioritization
    status = Column(String(10), nullable=False, index=True)  # success, failure, timeout
    input_data = Column(Text)  # JSON string of input
    output_data = Column(Text)  # JSON string of output
    error_message = Column(Text)
    processing_time_ms = Column(Integer)
    created_at = Column(DateTime, default=func.now(), index=True)
    
    # Relationships
    task = relationship("Task", back_populates="ai_logs")
    
    def __repr__(self):
        return f"<AIProcessingLog(id={self.id}, task_id={self.task_id}, type={self.processing_type})>"

# Database utility functions
def create_tables(engine):
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)

def get_default_categories():
    """Get default categories for initial database setup"""
    return [
        Category(name="Work", description="Professional and work-related tasks", color="#EF4444"),
        Category(name="Personal", description="Personal life and self-care tasks", color="#10B981"),
        Category(name="Learning", description="Educational and skill development tasks", color="#8B5CF6"),
        Category(name="Health", description="Health and fitness related tasks", color="#F59E0B"),
        Category(name="Finance", description="Financial planning and money management", color="#06B6D4"),
        Category(name="Home", description="Household and maintenance tasks", color="#84CC16"),
        Category(name="Social", description="Social activities and relationships", color="#F97316"),
        Category(name="Creative", description="Creative projects and hobbies", color="#EC4899"),
        Category(name="Travel", description="Travel planning and activities", color="#6366F1"),
        Category(name="Other", description="Miscellaneous tasks", color="#6B7280")
    ]

# Query optimization helpers
class QueryOptimizer:
    """Helper class for optimized database queries"""
    
    @staticmethod
    def get_user_tasks_optimized(db, user_id: str, status: Optional[str] = None, 
                               limit: int = 100, offset: int = 0):
        """Optimized query for user tasks with optional status filter"""
        query = db.query(Task).filter(Task.user_id == user_id)
        
        if status:
            query = query.filter(Task.status == status)
        
        return query.order_by(Task.priority.desc(), Task.created_at.desc())\
                   .offset(offset).limit(limit).all()
    
    @staticmethod
    def get_tasks_needing_ai_processing(db, limit: int = 10):
        """Get tasks that need AI processing"""
        return db.query(Task)\
                .filter(Task.ai_processing_status.in_([AIProcessingStatus.PENDING, AIProcessingStatus.FAILED]))\
                .order_by(Task.created_at.asc())\
                .limit(limit).all()
    
    @staticmethod
    def get_task_with_relations(db, task_id: str, user_id: str):
        """Get task with all related data in single query"""
        return db.query(Task)\
                .filter(Task.id == task_id, Task.user_id == user_id)\
                .first()