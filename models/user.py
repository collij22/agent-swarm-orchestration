"""
User model for authentication and authorization
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from models.base import BaseModel
import enum
from datetime import datetime
from typing import Optional


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class User(BaseModel):
    __tablename__ = "users"
    
    # Basic info
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Authentication
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth-only users
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    
    # OAuth integration
    github_id = Column(String(50), unique=True, nullable=True, index=True)
    google_id = Column(String(50), unique=True, nullable=True, index=True)
    
    # Profile
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    website = Column(String(255), nullable=True)
    location = Column(String(100), nullable=True)
    
    # Security
    last_login = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # API access
    api_key = Column(String(64), unique=True, nullable=True, index=True)
    api_key_created_at = Column(DateTime(timezone=True), nullable=True)
    
    def is_locked(self) -> bool:
        """Check if account is locked"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == UserRole.ADMIN
    
    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"