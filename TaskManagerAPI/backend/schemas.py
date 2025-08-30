from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enums
class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None

# Category schemas
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    color: str = Field(default="#3B82F6", regex="^#[0-9A-Fa-f]{6}$")

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Task schemas
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO

class TaskCreate(TaskBase):
    category_id: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    category_id: Optional[str] = None

class TaskResponse(TaskBase):
    id: str
    category_name: Optional[str] = None
    priority: int
    created_at: datetime
    updated_at: datetime
    user_id: str
    category_id: Optional[str] = None
    category: Optional[CategoryResponse] = None
    
    class Config:
        from_attributes = True

# AI schemas
class AICategorizationRequest(BaseModel):
    task_id: str

class AICategorizationResponse(BaseModel):
    task_id: str
    category: str
    confidence: int
    reasoning: str

class AIPrioritizationRequest(BaseModel):
    task_id: str

class AIPrioritizationResponse(BaseModel):
    task_id: str
    priority: int
    confidence: int
    reasoning: str

# Response schemas
class MessageResponse(BaseModel):
    message: str
    status: str = "success"

class ErrorResponse(BaseModel):
    detail: str
    status: str = "error"

# List responses
class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int
    page: int = 1
    size: int = 50

class CategoryListResponse(BaseModel):
    categories: List[CategoryResponse]
    total: int