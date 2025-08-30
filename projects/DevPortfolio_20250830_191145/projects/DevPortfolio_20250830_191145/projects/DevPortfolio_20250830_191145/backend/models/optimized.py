"""
Optimized Database Models
Designed for high-performance queries and <200ms API responses
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
import uuid

Base = declarative_base()

class BlogPost(Base):
    """
    Optimized blog post model with performance indexes
    """
    __tablename__ = "blog_posts"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core fields
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(Text)
    
    # Metadata
    status = Column(String(20), default="draft", index=True)  # draft, published, archived
    featured = Column(Boolean, default=False, index=True)
    
    # SEO and categorization
    tags = Column(ARRAY(String), default=[], index=True)  # GIN index for array queries
    categories = Column(ARRAY(String), default=[])
    meta_description = Column(String(160))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, index=True)
    
    # Analytics
    view_count = Column(Integer, default=0)
    read_time = Column(Integer)  # Estimated read time in minutes
    
    # AI-generated content
    ai_summary = Column(Text)
    ai_tags = Column(ARRAY(String), default=[])
    seo_score = Column(Integer, default=0)
    
    # Relationships
    comments = relationship("Comment", back_populates="post", lazy="dynamic")
    
    # Performance indexes
    __table_args__ = (
        # Composite index for published posts ordered by date
        Index('idx_published_posts_date', 'published_at', 'status', postgresql_where=(status == 'published')),
        
        # Index for featured posts
        Index('idx_featured_posts', 'featured', 'published_at', postgresql_where=(featured == True)),
        
        # Full-text search index (if using PostgreSQL)
        Index('idx_blog_search', 'title', 'content', postgresql_using='gin'),
        
        # Tag search optimization
        Index('idx_blog_tags', 'tags', postgresql_using='gin'),
    )


class Project(Base):
    """
    Optimized portfolio project model
    """
    __tablename__ = "projects"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core fields
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    short_description = Column(String(300))
    
    # URLs and links
    github_url = Column(String(500))
    demo_url = Column(String(500))
    image_url = Column(String(500))
    
    # Technical details
    technologies = Column(ARRAY(String), default=[], index=True)  # GIN index
    category = Column(String(100), index=True)
    difficulty = Column(String(20), default="intermediate")  # beginner, intermediate, advanced
    
    # Status and visibility
    status = Column(String(20), default="active", index=True)  # active, archived, private
    featured = Column(Boolean, default=False, index=True)
    priority = Column(Integer, default=0, index=True)  # Higher number = higher priority
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    project_date = Column(DateTime, index=True)  # When project was completed
    
    # GitHub integration
    github_stars = Column(Integer, default=0)
    github_forks = Column(Integer, default=0)
    github_last_updated = Column(DateTime)
    
    # Analytics
    view_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    
    # Performance indexes
    __table_args__ = (
        # Featured projects ordered by priority
        Index('idx_featured_projects', 'featured', 'priority', 'created_at'),
        
        # Technology search
        Index('idx_project_technologies', 'technologies', postgresql_using='gin'),
        
        # Category and status filtering
        Index('idx_project_category_status', 'category', 'status', 'featured'),
    )


class Skill(Base):
    """
    Developer skills with proficiency levels
    """
    __tablename__ = "skills"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core fields
    name = Column(String(100), nullable=False, unique=True)
    category = Column(String(100), nullable=False, index=True)  # Programming, Framework, Tool, etc.
    proficiency = Column(Integer, nullable=False)  # 1-10 scale
    
    # Display
    icon = Column(String(100))  # Icon class or URL
    color = Column(String(7))   # Hex color code
    description = Column(Text)
    
    # Experience
    years_experience = Column(Integer, default=0)
    last_used = Column(DateTime, index=True)
    
    # Visibility
    featured = Column(Boolean, default=False, index=True)
    display_order = Column(Integer, default=0, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Performance indexes
    __table_args__ = (
        # Featured skills ordered by proficiency
        Index('idx_featured_skills', 'featured', 'proficiency', 'display_order'),
        
        # Category grouping
        Index('idx_skills_category', 'category', 'proficiency'),
    )


class Experience(Base):
    """
    Professional experience timeline
    """
    __tablename__ = "experience"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core fields
    company = Column(String(200), nullable=False)
    position = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Dates
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, index=True)  # NULL for current position
    
    # Details
    location = Column(String(200))
    company_url = Column(String(500))
    company_logo = Column(String(500))
    
    # Achievements
    achievements = Column(JSON, default=[])  # List of achievement strings
    technologies = Column(ARRAY(String), default=[])
    
    # Display
    featured = Column(Boolean, default=False, index=True)
    display_order = Column(Integer, default=0, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Performance indexes
    __table_args__ = (
        # Timeline ordering (most recent first)
        Index('idx_experience_timeline', 'start_date', 'end_date'),
        
        # Featured experience
        Index('idx_featured_experience', 'featured', 'display_order'),
    )


class Comment(Base):
    """
    Blog comment system with moderation
    """
    __tablename__ = "comments"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core fields
    content = Column(Text, nullable=False)
    author_name = Column(String(100), nullable=False)
    author_email = Column(String(200), nullable=False)
    author_url = Column(String(500))
    
    # Moderation
    approved = Column(Boolean, default=False, index=True)
    spam_score = Column(Integer, default=0)  # 0-100, higher = more likely spam
    
    # Relationships
    post_id = Column(UUID(as_uuid=True), ForeignKey('blog_posts.id'), nullable=False, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('comments.id'))  # For nested comments
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    post = relationship("BlogPost", back_populates="comments")
    parent = relationship("Comment", remote_side=[id])
    replies = relationship("Comment", back_populates="parent")
    
    # Performance indexes
    __table_args__ = (
        # Approved comments for a post, ordered by date
        Index('idx_approved_comments', 'post_id', 'approved', 'created_at'),
        
        # Moderation queue
        Index('idx_moderation_queue', 'approved', 'spam_score', 'created_at'),
    )


class Analytics(Base):
    """
    Website analytics and metrics
    """
    __tablename__ = "analytics"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core fields
    path = Column(String(500), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # page_view, click, etc.
    
    # User information (anonymized)
    session_id = Column(String(100), index=True)
    user_agent = Column(Text)
    ip_hash = Column(String(64))  # Hashed IP for privacy
    
    # Location (if available)
    country = Column(String(2))
    city = Column(String(100))
    
    # Referrer information
    referrer = Column(String(500))
    utm_source = Column(String(100))
    utm_medium = Column(String(100))
    utm_campaign = Column(String(100))
    
    # Performance metrics
    page_load_time = Column(Integer)  # milliseconds
    time_on_page = Column(Integer)    # seconds
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    date = Column(DateTime, index=True)  # Date only for daily aggregation
    
    # Additional data
    metadata = Column(JSON, default={})
    
    # Performance indexes
    __table_args__ = (
        # Daily analytics queries
        Index('idx_analytics_daily', 'date', 'path', 'event_type'),
        
        # Path analytics
        Index('idx_analytics_path', 'path', 'timestamp'),
        
        # Session tracking
        Index('idx_analytics_session', 'session_id', 'timestamp'),
        
        # Performance monitoring
        Index('idx_analytics_performance', 'path', 'page_load_time', 'timestamp'),
    )


class Cache(Base):
    """
    Database-level cache for expensive computations
    """
    __tablename__ = "cache"
    
    # Primary key
    cache_key = Column(String(255), primary_key=True)
    
    # Cache data
    data = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    hit_count = Column(Integer, default=0)
    
    # Performance indexes
    __table_args__ = (
        # Expiration cleanup
        Index('idx_cache_expiration', 'expires_at'),
        
        # Popular cache entries
        Index('idx_cache_popular', 'hit_count', 'expires_at'),
    )