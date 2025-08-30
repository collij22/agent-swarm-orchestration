"""
SQLAlchemy models for TaskManagerAPI
Defines ORM models with relationships and validation
"""

from sqlalchemy import (
    Column, String, Text, Integer, DateTime, Boolean, Float,
    ForeignKey, CheckConstraint, Index, event
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List
import uuid
import re

Base = declarative_base()

class User(Base):
    """User model for authentication and task ownership"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    task_history = relationship("TaskHistory", back_populates="user")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('length(username) >= 3 AND length(username) <= 50', name='chk_username_length'),
        CheckConstraint("email LIKE '%_@_%._%'", name='chk_email_format'),
        Index('idx_users_username', 'username'),
        Index('idx_users_email', 'email'),
    )
    
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format"""
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError("Invalid email format")
        return email
    
    @validates('username')
    def validate_username(self, key, username):
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_]{3,50}$', username):
            raise ValueError("Username must be 3-50 characters, alphanumeric and underscore only")
        return username

class Category(Base):
    """Category model for task classification"""
    __tablename__ = "categories"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    color = Column(String(7), default='#3B82F6')  # Hex color code
    created_at = Column(DateTime, default=func.now())
    is_system_generated = Column(Boolean, default=False)
    
    # Relationships
    tasks = relationship("Task", back_populates="category")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('length(name) >= 2 AND length(name) <= 50', name='chk_category_name_length'),
        CheckConstraint("color GLOB '#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]'", name='chk_color_format'),
    )
    
    @validates('color')
    def validate_color(self, key, color):
        """Validate hex color format"""
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            raise ValueError("Color must be in hex format (#RRGGBB)")
        return color

class Task(Base):
    """Task model - core entity for task management"""
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category_id = Column(String, ForeignKey('categories.id', ondelete='SET NULL'))
    priority = Column(Integer, default=3)  # 1-5 scale
    status = Column(String(20), default='todo')
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    
    # AI enhancement fields
    ai_category_confidence = Column(Float)  # 0.0-1.0
    ai_priority_score = Column(Float)
    ai_last_processed = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    category = relationship("Category", back_populates="tasks")
    history = relationship("TaskHistory", back_populates="task", cascade="all, delete-orphan")
    ai_queue_items = relationship("AIProcessingQueue", back_populates="task", cascade="all, delete-orphan")
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint('length(title) >= 1 AND length(title) <= 200', name='chk_title_length'),
        CheckConstraint('priority >= 1 AND priority <= 5', name='chk_priority_range'),
        CheckConstraint("status IN ('todo', 'in_progress', 'done')", name='chk_status_values'),
        CheckConstraint('ai_category_confidence IS NULL OR (ai_category_confidence >= 0.0 AND ai_category_confidence <= 1.0)', name='chk_ai_confidence'),
        
        # Performance indexes
        Index('idx_tasks_user_id', 'user_id'),
        Index('idx_tasks_user_status', 'user_id', 'status'),
        Index('idx_tasks_user_created', 'user_id', 'created_at'),
        Index('idx_tasks_category', 'category_id'),
        Index('idx_tasks_category_status', 'category_id', 'status'),
        Index('idx_tasks_priority', 'priority'),
        Index('idx_tasks_due_date', 'due_date'),
        Index('idx_tasks_status_updated', 'status', 'updated_at'),
        Index('idx_tasks_ai_processing', 'ai_last_processed'),
    )
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate status values"""
        valid_statuses = ['todo', 'in_progress', 'done']
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return status
    
    @validates('priority')
    def validate_priority(self, key, priority):
        """Validate priority range"""
        if priority < 1 or priority > 5:
            raise ValueError("Priority must be between 1 and 5")
        return priority
    
    def mark_completed(self):
        """Mark task as completed with timestamp"""
        self.status = 'done'
        self.completed_at = func.now()

class TaskHistory(Base):
    """Task history model for audit trail"""
    __tablename__ = "task_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    action = Column(String(20), nullable=False)
    old_values = Column(Text)  # JSON string
    new_values = Column(Text)  # JSON string
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="history")
    user = relationship("User", back_populates="task_history")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("action IN ('created', 'updated', 'status_changed', 'deleted')", name='chk_action_values'),
        Index('idx_task_history_task', 'task_id', 'created_at'),
        Index('idx_task_history_user', 'user_id', 'created_at'),
    )

class AIProcessingQueue(Base):
    """AI processing queue for async AI operations"""
    __tablename__ = "ai_processing_queue"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    processing_type = Column(String(20), nullable=False)
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Relationships
    task = relationship("Task", back_populates="ai_queue_items")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("processing_type IN ('categorization', 'priority_scoring')", name='chk_processing_type'),
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name='chk_queue_status'),
        Index('idx_ai_queue_status', 'status', 'created_at'),
    )

# Event listeners for automatic updates
@event.listens_for(Task.status, 'set')
def task_status_changed(target, value, oldvalue, initiator):
    """Automatically set completed_at when status changes to 'done'"""
    if value == 'done' and oldvalue != 'done':
        target.completed_at = func.now()
    elif value != 'done':
        target.completed_at = None

# Database utility functions
def get_user_tasks_query(db_session, user_id: str, status: Optional[str] = None, 
                        category_id: Optional[str] = None, limit: int = 100):
    """Optimized query for user tasks with optional filtering"""
    query = db_session.query(Task).filter(Task.user_id == user_id)
    
    if status:
        query = query.filter(Task.status == status)
    
    if category_id:
        query = query.filter(Task.category_id == category_id)
    
    return query.order_by(Task.priority.desc(), Task.created_at.desc()).limit(limit)

def get_tasks_needing_ai_processing(db_session, processing_type: str, limit: int = 10):
    """Get tasks that need AI processing"""
    return db_session.query(Task).filter(
        Task.ai_last_processed.is_(None)
    ).order_by(Task.created_at.asc()).limit(limit)