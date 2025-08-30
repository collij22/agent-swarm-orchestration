"""
Database Models for DevPortfolio
SQLAlchemy models for portfolio, blog, user, and analytics data
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    """Admin user model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # OAuth integration
    github_id = Column(String(100), unique=True)
    google_id = Column(String(100), unique=True)
    avatar_url = Column(String(500))
    
    # Relationships
    blog_posts = relationship("BlogPost", back_populates="author")
    analytics_events = relationship("AnalyticsEvent", back_populates="user")

class Project(Base):
    """Portfolio project model"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    short_description = Column(String(500))
    
    # GitHub integration
    github_url = Column(String(500))
    github_repo_id = Column(String(100))
    github_stars = Column(Integer, default=0)
    github_forks = Column(Integer, default=0)
    
    # Project details
    demo_url = Column(String(500))
    image_url = Column(String(500))
    technologies = Column(JSON)  # Array of technology tags
    category = Column(String(100))
    status = Column(String(50), default="active")  # active, archived, featured
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sort_order = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    
    # Analytics
    view_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)

class Skill(Base):
    """Skills and proficiency model"""
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    category = Column(String(100))  # Frontend, Backend, DevOps, etc.
    proficiency_level = Column(Integer, default=1)  # 1-5 scale
    years_experience = Column(Float)
    description = Column(Text)
    icon_url = Column(String(500))
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

class Experience(Base):
    """Work experience timeline model"""
    __tablename__ = "experiences"
    
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(200), nullable=False)
    position = Column(String(200), nullable=False)
    description = Column(Text)
    achievements = Column(JSON)  # Array of achievement strings
    
    # Dates
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)  # Null for current position
    is_current = Column(Boolean, default=False)
    
    # Company details
    company_url = Column(String(500))
    company_logo = Column(String(500))
    location = Column(String(200))
    
    # Technologies used
    technologies = Column(JSON)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    sort_order = Column(Integer, default=0)

class BlogPost(Base):
    """Blog post model with AI assistance"""
    __tablename__ = "blog_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    slug = Column(String(300), unique=True, index=True, nullable=False)
    content = Column(Text, nullable=False)
    excerpt = Column(String(500))
    
    # AI-powered features
    ai_suggestions = Column(JSON)  # AI content suggestions
    seo_score = Column(Integer, default=0)
    readability_score = Column(Integer, default=0)
    auto_tags = Column(JSON)  # AI-generated tags
    
    # Metadata
    status = Column(String(50), default="draft")  # draft, published, archived
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Categories and tags
    category = Column(String(100))
    tags = Column(JSON)  # Array of tag strings
    
    # SEO
    meta_description = Column(String(300))
    featured_image = Column(String(500))
    
    # Analytics
    view_count = Column(Integer, default=0)
    read_time_minutes = Column(Integer)
    
    # Author relationship
    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User", back_populates="blog_posts")
    
    # Comments relationship
    comments = relationship("Comment", back_populates="post")

class Comment(Base):
    """Blog comment system with moderation"""
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    author_name = Column(String(100), nullable=False)
    author_email = Column(String(255), nullable=False)
    author_website = Column(String(500))
    
    # Moderation
    status = Column(String(50), default="pending")  # pending, approved, spam, rejected
    is_spam = Column(Boolean, default=False)
    spam_score = Column(Float, default=0.0)
    
    # Nested comments
    parent_id = Column(Integer, ForeignKey("comments.id"))
    parent = relationship("Comment", remote_side=[id])
    
    # Post relationship
    post_id = Column(Integer, ForeignKey("blog_posts.id"))
    post = relationship("BlogPost", back_populates="comments")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ip_address = Column(String(45))  # IPv6 support

class ContactMessage(Base):
    """Contact form submissions"""
    __tablename__ = "contact_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(255), nullable=False)
    subject = Column(String(300))
    message = Column(Text, nullable=False)
    
    # Metadata
    status = Column(String(50), default="unread")  # unread, read, replied, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))
    
    # Spam protection
    is_spam = Column(Boolean, default=False)
    spam_score = Column(Float, default=0.0)

class AnalyticsEvent(Base):
    """Analytics tracking for visitor behavior"""
    __tablename__ = "analytics_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False)  # page_view, blog_read, project_view
    page_path = Column(String(500))
    referrer = Column(String(500))
    
    # Visitor information
    visitor_id = Column(String(100))  # Anonymous visitor tracking
    session_id = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(String(1000))
    
    # Geographic data
    country = Column(String(100))
    city = Column(String(100))
    
    # Engagement metrics
    duration_seconds = Column(Integer)
    scroll_percentage = Column(Integer)
    
    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # User relationship (for authenticated users)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="analytics_events")

class APIKey(Base):
    """API key management for external integrations"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False)
    service = Column(String(100))  # github, openai, etc.
    
    # Permissions and limits
    permissions = Column(JSON)
    rate_limit_per_minute = Column(Integer, default=60)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    expires_at = Column(DateTime)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_usage_reset = Column(DateTime, default=datetime.utcnow)