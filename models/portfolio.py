"""
Portfolio models for project showcase system
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from models.base import BaseModel
from typing import List, Optional, Dict, Any


# Association table for project-technology many-to-many relationship
project_technology = Table(
    'project_technology',
    BaseModel.metadata,
    Column('project_id', String(36), ForeignKey('projects.id'), primary_key=True),
    Column('technology_id', String(36), ForeignKey('technologies.id'), primary_key=True)
)


class Technology(BaseModel):
    __tablename__ = "technologies"
    
    name = Column(String(50), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False)  # frontend, backend, database, devops, etc.
    icon_url = Column(String(500), nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    description = Column(Text, nullable=True)
    
    # Relationships
    projects = relationship("Project", secondary=project_technology, back_populates="technologies")
    skills = relationship("Skill", back_populates="technology")
    
    def __repr__(self):
        return f"<Technology(name={self.name}, category={self.category})>"


class Project(BaseModel):
    __tablename__ = "projects"
    
    # Basic info
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    short_description = Column(String(500), nullable=True)
    
    # Content
    content = Column(Text, nullable=True)  # Markdown content
    featured_image = Column(String(500), nullable=True)
    gallery = Column(JSON, nullable=True)  # Array of image URLs
    
    # Links
    live_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    demo_video_url = Column(String(500), nullable=True)
    
    # GitHub integration
    github_repo = Column(String(200), nullable=True)  # owner/repo format
    github_data = Column(JSON, nullable=True)  # Cached GitHub API data
    github_last_sync = Column(DateTime(timezone=True), nullable=True)
    
    # Status and visibility
    is_featured = Column(Boolean, default=False, nullable=False)
    is_published = Column(Boolean, default=True, nullable=False)
    status = Column(String(20), default="active", nullable=False)  # active, archived, wip
    
    # Metrics
    view_count = Column(Integer, default=0, nullable=False)
    like_count = Column(Integer, default=0, nullable=False)
    
    # Sorting and categorization
    order_index = Column(Integer, default=0, nullable=False)
    category = Column(String(50), nullable=True)
    
    # Relationships
    technologies = relationship("Technology", secondary=project_technology, back_populates="projects")
    
    def __repr__(self):
        return f"<Project(title={self.title}, status={self.status})>"


class Skill(BaseModel):
    __tablename__ = "skills"
    
    technology_id = Column(String(36), ForeignKey('technologies.id'), nullable=False)
    
    # Proficiency
    proficiency_level = Column(Integer, nullable=False)  # 1-10 scale
    years_experience = Column(Integer, nullable=False)
    
    # Context
    description = Column(Text, nullable=True)
    projects_count = Column(Integer, default=0, nullable=False)
    
    # Validation
    is_primary = Column(Boolean, default=False, nullable=False)  # Primary skills
    is_learning = Column(Boolean, default=False, nullable=False)  # Currently learning
    
    # Relationships
    technology = relationship("Technology", back_populates="skills")
    
    def __repr__(self):
        return f"<Skill(technology={self.technology.name if self.technology else 'Unknown'}, level={self.proficiency_level})>"


class Experience(BaseModel):
    __tablename__ = "experiences"
    
    # Company info
    company = Column(String(200), nullable=False)
    position = Column(String(200), nullable=False)
    company_url = Column(String(500), nullable=True)
    company_logo = Column(String(500), nullable=True)
    
    # Duration
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)  # Null for current position
    is_current = Column(Boolean, default=False, nullable=False)
    
    # Details
    description = Column(Text, nullable=False)
    achievements = Column(JSON, nullable=True)  # Array of achievement strings
    location = Column(String(100), nullable=True)
    employment_type = Column(String(50), nullable=True)  # full-time, part-time, contract, etc.
    
    # Technologies used
    technologies_used = Column(JSON, nullable=True)  # Array of technology names
    
    def __repr__(self):
        return f"<Experience(company={self.company}, position={self.position})>"