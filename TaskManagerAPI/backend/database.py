from sqlalchemy import create_engine, Column, String, Text, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from datetime import datetime

# Database URL
DATABASE_URL = "sqlite:///./taskmanager.db"

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Enums
class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

# Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    color = Column(String(7), default="#3B82F6")  # Default blue color
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    tasks = relationship("Task", back_populates="category")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category_name = Column(String(50), nullable=True)  # AI-generated category
    priority = Column(Integer, default=3)  # 1-5 scale, AI-scored
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    category = relationship("Category", back_populates="tasks")

class AILog(Base):
    __tablename__ = "ai_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    operation = Column(String(50), nullable=False)  # categorize, prioritize
    input_data = Column(Text, nullable=False)
    output_data = Column(Text, nullable=False)
    confidence_score = Column(Integer, default=0)  # 0-100
    created_at = Column(DateTime, default=func.now())

# Database functions
def init_db():
    """Initialize database and create tables"""
    Base.metadata.create_all(bind=engine)
    
    # Create default categories
    db = SessionLocal()
    try:
        if not db.query(Category).first():
            default_categories = [
                Category(name="Work", description="Work-related tasks", color="#EF4444"),
                Category(name="Personal", description="Personal tasks", color="#10B981"),
                Category(name="Shopping", description="Shopping lists", color="#F59E0B"),
                Category(name="Health", description="Health and fitness", color="#8B5CF6"),
                Category(name="Learning", description="Learning and education", color="#06B6D4"),
            ]
            for cat in default_categories:
                db.add(cat)
            db.commit()
    finally:
        db.close()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()