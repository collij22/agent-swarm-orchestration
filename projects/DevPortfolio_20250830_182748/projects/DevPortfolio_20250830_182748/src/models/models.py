from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    bio = Column(Text)
    location = Column(String(100))
    website = Column(String(255))
    github_username = Column(String(50))
    linkedin_url = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    projects = relationship("Project", back_populates="owner")
    blog_posts = relationship("BlogPost", back_populates="author")
    skills = relationship("Skill", back_populates="user")
    experiences = relationship("Experience", back_populates="user")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    long_description = Column(Text)
    github_url = Column(String(255))
    demo_url = Column(String(255))
    image_url = Column(String(255))
    technologies = Column(JSON)  # List of technology names
    category = Column(String(50))
    status = Column(String(20), default="active")  # active, archived, featured
    is_featured = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign Keys
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    owner = relationship("User", back_populates="projects")

class BlogPost(Base):
    __tablename__ = "blog_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, index=True, nullable=False)
    excerpt = Column(Text)
    content = Column(Text, nullable=False)
    featured_image = Column(String(255))
    tags = Column(JSON)  # List of tag names
    category = Column(String(50))
    status = Column(String(20), default="draft")  # draft, published, archived
    is_featured = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    read_time = Column(Integer)  # Estimated read time in minutes
    seo_title = Column(String(200))
    seo_description = Column(Text)
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign Keys
    author_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    author = relationship("User", back_populates="blog_posts")
    comments = relationship("Comment", back_populates="blog_post")

class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    author_name = Column(String(100), nullable=False)
    author_email = Column(String(100), nullable=False)
    author_website = Column(String(255))
    is_approved = Column(Boolean, default=False)
    is_spam = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign Keys
    blog_post_id = Column(Integer, ForeignKey("blog_posts.id"))
    parent_id = Column(Integer, ForeignKey("comments.id"))
    
    # Relationships
    blog_post = relationship("BlogPost", back_populates="comments")
    parent = relationship("Comment", remote_side=[id])

class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50))  # Frontend, Backend, DevOps, etc.
    proficiency = Column(Integer)  # 1-10 scale
    years_experience = Column(Integer)
    is_featured = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", back_populates="skills")

class Experience(Base):
    __tablename__ = "experiences"
    
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(100), nullable=False)
    position = Column(String(100), nullable=False)
    description = Column(Text)
    achievements = Column(JSON)  # List of achievement strings
    technologies = Column(JSON)  # List of technology names
    location = Column(String(100))
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    is_current = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", back_populates="experiences")

class Analytics(Base):
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False)  # page_view, project_click, etc.
    page_path = Column(String(255))
    user_agent = Column(String(500))
    ip_address = Column(String(45))
    referrer = Column(String(255))
    metadata = Column(JSON)  # Additional event data
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    subject = Column(String(200))
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    is_replied = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())