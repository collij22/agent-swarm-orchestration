from pydantic import BaseModel, EmailStr, HttpUrl, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Base schemas
class TimestampMixin(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[HttpUrl] = None
    github_username: Optional[str] = None
    linkedin_url: Optional[HttpUrl] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[HttpUrl] = None
    github_username: Optional[str] = None
    linkedin_url: Optional[HttpUrl] = None

class UserResponse(UserBase, TimestampMixin):
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True

class UserProfile(UserResponse):
    projects_count: Optional[int] = 0
    blog_posts_count: Optional[int] = 0

# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str  # Can be username or email
    password: str

# Project schemas
class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    FEATURED = "featured"

class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    long_description: Optional[str] = None
    github_url: Optional[HttpUrl] = None
    demo_url: Optional[HttpUrl] = None
    image_url: Optional[HttpUrl] = None
    technologies: Optional[List[str]] = []
    category: Optional[str] = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    is_featured: bool = False
    order_index: int = 0

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    long_description: Optional[str] = None
    github_url: Optional[HttpUrl] = None
    demo_url: Optional[HttpUrl] = None
    image_url: Optional[HttpUrl] = None
    technologies: Optional[List[str]] = None
    category: Optional[str] = None
    status: Optional[ProjectStatus] = None
    is_featured: Optional[bool] = None
    order_index: Optional[int] = None

class ProjectResponse(ProjectBase, TimestampMixin):
    id: int
    owner_id: int
    
    class Config:
        from_attributes = True

# Blog schemas
class BlogStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class BlogPostBase(BaseModel):
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str
    featured_image: Optional[HttpUrl] = None
    tags: Optional[List[str]] = []
    category: Optional[str] = None
    status: BlogStatus = BlogStatus.DRAFT
    is_featured: bool = False
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None

class BlogPostCreate(BlogPostBase):
    @validator('slug')
    def validate_slug(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Slug must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower()

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    featured_image: Optional[HttpUrl] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    status: Optional[BlogStatus] = None
    is_featured: Optional[bool] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None

class BlogPostResponse(BlogPostBase, TimestampMixin):
    id: int
    author_id: int
    view_count: int
    read_time: Optional[int]
    published_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class BlogPostSummary(BaseModel):
    id: int
    title: str
    slug: str
    excerpt: Optional[str]
    featured_image: Optional[HttpUrl]
    tags: Optional[List[str]]
    category: Optional[str]
    view_count: int
    read_time: Optional[int]
    published_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Comment schemas
class CommentBase(BaseModel):
    content: str
    author_name: str
    author_email: EmailStr
    author_website: Optional[HttpUrl] = None

class CommentCreate(CommentBase):
    blog_post_id: int
    parent_id: Optional[int] = None

class CommentResponse(CommentBase, TimestampMixin):
    id: int
    blog_post_id: int
    parent_id: Optional[int]
    is_approved: bool
    
    class Config:
        from_attributes = True

# Skill schemas
class SkillBase(BaseModel):
    name: str
    category: Optional[str] = None
    proficiency: int
    years_experience: Optional[int] = None
    is_featured: bool = False
    order_index: int = 0
    
    @validator('proficiency')
    def validate_proficiency(cls, v):
        if v < 1 or v > 10:
            raise ValueError('Proficiency must be between 1 and 10')
        return v

class SkillCreate(SkillBase):
    pass

class SkillUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    proficiency: Optional[int] = None
    years_experience: Optional[int] = None
    is_featured: Optional[bool] = None
    order_index: Optional[int] = None

class SkillResponse(SkillBase):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True

# Experience schemas
class ExperienceBase(BaseModel):
    company: str
    position: str
    description: Optional[str] = None
    achievements: Optional[List[str]] = []
    technologies: Optional[List[str]] = []
    location: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_current: bool = False
    order_index: int = 0

class ExperienceCreate(ExperienceBase):
    pass

class ExperienceUpdate(BaseModel):
    company: Optional[str] = None
    position: Optional[str] = None
    description: Optional[str] = None
    achievements: Optional[List[str]] = None
    technologies: Optional[List[str]] = None
    location: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_current: Optional[bool] = None
    order_index: Optional[int] = None

class ExperienceResponse(ExperienceBase):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True

# Contact schemas
class ContactCreate(BaseModel):
    name: str
    email: EmailStr
    subject: Optional[str] = None
    message: str

class ContactResponse(ContactCreate, TimestampMixin):
    id: int
    is_read: bool
    is_replied: bool
    
    class Config:
        from_attributes = True

# Analytics schemas
class AnalyticsEvent(BaseModel):
    event_type: str
    page_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class AnalyticsResponse(BaseModel):
    total_views: int
    unique_visitors: int
    popular_pages: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]

# AI Assistant schemas
class AIContentRequest(BaseModel):
    prompt: str
    content_type: str = "blog_post"  # blog_post, project_description, bio
    max_tokens: int = 500

class AIContentResponse(BaseModel):
    generated_content: str
    suggestions: Optional[List[str]] = []

# Search schemas
class SearchQuery(BaseModel):
    q: str
    category: Optional[str] = None
    limit: int = 10

class SearchResult(BaseModel):
    type: str  # "project" or "blog_post"
    id: int
    title: str
    description: str
    url: str
    relevance_score: float