"""
Blog models for markdown-based blog engine
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, Table, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON, ARRAY
from models.base import BaseModel
import enum
from datetime import datetime
from typing import List, Optional, Dict


# Association table for post-tag many-to-many relationship
post_tag = Table(
    'post_tag',
    BaseModel.metadata,
    Column('post_id', String(36), ForeignKey('posts.id'), primary_key=True),
    Column('tag_id', String(36), ForeignKey('tags.id'), primary_key=True)
)


class PostStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    SCHEDULED = "scheduled"


class CommentStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SPAM = "spam"


class Category(BaseModel):
    __tablename__ = "categories"
    
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    icon = Column(String(50), nullable=True)  # Icon name or emoji
    
    # SEO
    meta_title = Column(String(200), nullable=True)
    meta_description = Column(String(500), nullable=True)
    
    # Stats
    post_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    posts = relationship("Post", back_populates="category")
    
    def __repr__(self):
        return f"<Category(name={self.name}, posts={self.post_count})>"


class Tag(BaseModel):
    __tablename__ = "tags"
    
    name = Column(String(50), unique=True, nullable=False, index=True)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)
    
    # Stats
    post_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    posts = relationship("Post", secondary=post_tag, back_populates="tags")
    
    def __repr__(self):
        return f"<Tag(name={self.name}, posts={self.post_count})>"


class Post(BaseModel):
    __tablename__ = "posts"
    
    # Basic info
    title = Column(String(300), nullable=False)
    slug = Column(String(300), unique=True, nullable=False, index=True)
    excerpt = Column(Text, nullable=True)
    
    # Content
    content = Column(Text, nullable=False)  # Markdown content
    html_content = Column(Text, nullable=True)  # Rendered HTML (cached)
    featured_image = Column(String(500), nullable=True)
    
    # Publishing
    status = Column(Enum(PostStatus), default=PostStatus.DRAFT, nullable=False, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    
    # SEO
    meta_title = Column(String(200), nullable=True)
    meta_description = Column(String(500), nullable=True)
    canonical_url = Column(String(500), nullable=True)
    
    # Features
    is_featured = Column(Boolean, default=False, nullable=False)
    allow_comments = Column(Boolean, default=True, nullable=False)
    is_pinned = Column(Boolean, default=False, nullable=False)
    
    # Metrics
    view_count = Column(Integer, default=0, nullable=False)
    like_count = Column(Integer, default=0, nullable=False)
    comment_count = Column(Integer, default=0, nullable=False)
    reading_time = Column(Integer, nullable=True)  # Estimated reading time in minutes
    
    # AI assistance data
    ai_suggestions = Column(JSON, nullable=True)  # Store AI suggestions
    seo_score = Column(Integer, nullable=True)  # SEO score from AI analysis
    readability_score = Column(Integer, nullable=True)
    
    # Relationships
    category_id = Column(String(36), ForeignKey('categories.id'), nullable=True)
    author_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    
    category = relationship("Category", back_populates="posts")
    author = relationship("User")
    tags = relationship("Tag", secondary=post_tag, back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    
    @property
    def is_published(self) -> bool:
        """Check if post is published"""
        return (
            self.status == PostStatus.PUBLISHED and
            self.published_at is not None and
            self.published_at <= datetime.utcnow()
        )
    
    def __repr__(self):
        return f"<Post(title={self.title}, status={self.status})>"


class Comment(BaseModel):
    __tablename__ = "comments"
    
    # Basic info
    post_id = Column(String(36), ForeignKey('posts.id'), nullable=False)
    parent_id = Column(String(36), ForeignKey('comments.id'), nullable=True)  # For nested comments
    
    # Author info (can be anonymous)
    author_name = Column(String(100), nullable=False)
    author_email = Column(String(255), nullable=False)
    author_website = Column(String(255), nullable=True)
    author_ip = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    
    # Content
    content = Column(Text, nullable=False)  # Markdown supported
    html_content = Column(Text, nullable=True)  # Rendered HTML
    
    # Moderation
    status = Column(Enum(CommentStatus), default=CommentStatus.PENDING, nullable=False)
    spam_score = Column(Integer, default=0, nullable=False)  # AI spam detection score
    moderation_notes = Column(Text, nullable=True)
    moderated_by = Column(String(36), ForeignKey('users.id'), nullable=True)
    moderated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    post = relationship("Post", back_populates="comments")
    parent = relationship("Comment", remote_side="Comment.id")
    children = relationship("Comment", cascade="all, delete-orphan")
    moderator = relationship("User")
    
    @property
    def is_approved(self) -> bool:
        """Check if comment is approved"""
        return self.status == CommentStatus.APPROVED
    
    def __repr__(self):
        return f"<Comment(author={self.author_name}, status={self.status})>"