"""
Analytics models for visitor tracking and metrics
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON, INET
from models.base import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class PageView(BaseModel):
    __tablename__ = "page_views"
    
    # Page info
    path = Column(String(500), nullable=False, index=True)
    title = Column(String(500), nullable=True)
    referrer = Column(String(500), nullable=True)
    
    # Visitor info
    visitor_id = Column(String(64), nullable=False, index=True)  # Hashed visitor ID
    session_id = Column(String(64), nullable=False, index=True)
    ip_address = Column(INET, nullable=True)  # Anonymized/hashed
    
    # Device info
    user_agent = Column(String(1000), nullable=True)
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    screen_resolution = Column(String(20), nullable=True)
    
    # Geographic info
    country = Column(String(2), nullable=True)  # ISO country code
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True)
    
    # Engagement metrics
    time_on_page = Column(Integer, nullable=True)  # Seconds
    bounce = Column(Boolean, default=False, nullable=False)
    
    # UTM parameters
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)
    utm_term = Column(String(100), nullable=True)
    utm_content = Column(String(100), nullable=True)
    
    # Additional data
    custom_data = Column(JSON, nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_pageviews_date_path', 'created_at', 'path'),
        Index('ix_pageviews_visitor_date', 'visitor_id', 'created_at'),
        Index('ix_pageviews_session_date', 'session_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<PageView(path={self.path}, visitor={self.visitor_id[:8]})>"


class Visitor(BaseModel):
    __tablename__ = "visitors"
    
    # Visitor identification (hashed)
    visitor_id = Column(String(64), unique=True, nullable=False, index=True)
    
    # First visit info
    first_visit = Column(DateTime(timezone=True), nullable=False, index=True)
    last_visit = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Counts
    visit_count = Column(Integer, default=1, nullable=False)
    page_view_count = Column(Integer, default=0, nullable=False)
    
    # Device info (from first visit)
    first_device_type = Column(String(50), nullable=True)
    first_browser = Column(String(100), nullable=True)
    first_os = Column(String(100), nullable=True)
    
    # Geographic info (from first visit)
    first_country = Column(String(2), nullable=True)
    first_region = Column(String(100), nullable=True)
    first_city = Column(String(100), nullable=True)
    
    # Traffic source (from first visit)
    first_referrer = Column(String(500), nullable=True)
    first_utm_source = Column(String(100), nullable=True)
    first_utm_medium = Column(String(100), nullable=True)
    first_utm_campaign = Column(String(100), nullable=True)
    
    # Engagement
    total_time_on_site = Column(Integer, default=0, nullable=False)  # Total seconds
    bounce_rate = Column(Integer, default=0, nullable=False)  # Percentage
    
    def __repr__(self):
        return f"<Visitor(id={self.visitor_id[:8]}, visits={self.visit_count})>"


class PopularContent(BaseModel):
    __tablename__ = "popular_content"
    
    # Content identification
    content_type = Column(String(50), nullable=False, index=True)  # post, project, page
    content_id = Column(String(36), nullable=True)  # Reference to actual content
    path = Column(String(500), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    
    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    
    # Metrics
    view_count = Column(Integer, default=0, nullable=False)
    unique_visitors = Column(Integer, default=0, nullable=False)
    avg_time_on_page = Column(Integer, default=0, nullable=False)
    bounce_rate = Column(Integer, default=0, nullable=False)
    
    # Rankings
    rank = Column(Integer, nullable=True)
    rank_change = Column(Integer, default=0, nullable=False)  # Change from previous period
    
    # Indexes
    __table_args__ = (
        Index('ix_popular_content_period', 'period_type', 'period_start', 'period_end'),
        Index('ix_popular_content_rank', 'period_type', 'rank'),
    )
    
    def __repr__(self):
        return f"<PopularContent(title={self.title}, views={self.view_count})>"


class GitHubActivity(BaseModel):
    __tablename__ = "github_activity"
    
    # GitHub data
    github_username = Column(String(100), nullable=False, index=True)
    activity_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Contribution data
    contributions = Column(Integer, default=0, nullable=False)
    commits = Column(Integer, default=0, nullable=False)
    pull_requests = Column(Integer, default=0, nullable=False)
    issues = Column(Integer, default=0, nullable=False)
    
    # Repository data
    repositories_data = Column(JSON, nullable=True)  # Top repositories for the day
    languages_data = Column(JSON, nullable=True)    # Language breakdown
    
    # Streak data
    current_streak = Column(Integer, default=0, nullable=False)
    longest_streak = Column(Integer, default=0, nullable=False)
    
    # Raw GitHub API response (cached)
    raw_data = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<GitHubActivity(date={self.activity_date.date()}, contributions={self.contributions})>"