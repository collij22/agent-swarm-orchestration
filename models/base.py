"""
Base model with common fields and utilities
"""

from sqlalchemy import Column, Integer, DateTime, String, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declared_attr
from database import Base
import uuid


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class UUIDMixin:
    """Mixin for UUID primary key"""
    
    @declared_attr
    def id(cls):
        return Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))


class BaseModel(Base, TimestampMixin, UUIDMixin):
    """Base model with common fields"""
    
    __abstract__ = True
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"