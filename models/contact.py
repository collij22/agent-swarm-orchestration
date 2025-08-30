"""
Contact models for contact form and notifications
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum, Integer
from sqlalchemy.dialects.postgresql import JSON, INET
from models.base import BaseModel
import enum
from datetime import datetime


class ContactStatus(str, enum.Enum):
    NEW = "new"
    READ = "read"
    REPLIED = "replied"
    ARCHIVED = "archived"
    SPAM = "spam"


class ContactType(str, enum.Enum):
    GENERAL = "general"
    PROJECT = "project"
    COLLABORATION = "collaboration"
    HIRING = "hiring"
    SUPPORT = "support"
    OTHER = "other"


class Contact(BaseModel):
    __tablename__ = "contacts"
    
    # Contact info
    name = Column(String(200), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    company = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Message
    subject = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)
    contact_type = Column(Enum(ContactType), default=ContactType.GENERAL, nullable=False)
    
    # Status and processing
    status = Column(Enum(ContactStatus), default=ContactStatus.NEW, nullable=False, index=True)
    priority = Column(Integer, default=1, nullable=False)  # 1=low, 2=medium, 3=high
    
    # Spam detection
    spam_score = Column(Integer, default=0, nullable=False)
    is_spam = Column(Boolean, default=False, nullable=False)
    spam_reason = Column(String(500), nullable=True)
    
    # Technical info
    ip_address = Column(INET, nullable=True)
    user_agent = Column(String(1000), nullable=True)
    referrer = Column(String(500), nullable=True)
    
    # reCAPTCHA
    recaptcha_score = Column(Float, nullable=True)
    recaptcha_action = Column(String(100), nullable=True)
    
    # Response tracking
    responded_at = Column(DateTime(timezone=True), nullable=True)
    response_count = Column(Integer, default=0, nullable=False)
    last_response_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional data
    form_data = Column(JSON, nullable=True)  # Additional form fields
    notes = Column(Text, nullable=True)  # Admin notes
    
    @property
    def is_new(self) -> bool:
        """Check if contact is new/unread"""
        return self.status == ContactStatus.NEW
    
    @property
    def needs_response(self) -> bool:
        """Check if contact needs response"""
        return self.status in [ContactStatus.NEW, ContactStatus.READ]
    
    def mark_as_read(self):
        """Mark contact as read"""
        if self.status == ContactStatus.NEW:
            self.status = ContactStatus.READ
    
    def mark_as_replied(self):
        """Mark contact as replied"""
        self.status = ContactStatus.REPLIED
        self.responded_at = datetime.utcnow()
        self.response_count += 1
        self.last_response_at = datetime.utcnow()
    
    def __repr__(self):
        return f"<Contact(name={self.name}, email={self.email}, status={self.status})>"


class NewsletterSubscriber(BaseModel):
    __tablename__ = "newsletter_subscribers"
    
    # Subscriber info
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_confirmed = Column(Boolean, default=False, nullable=False)
    
    # Subscription details
    subscribed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    unsubscribed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Preferences
    frequency = Column(String(20), default="weekly", nullable=False)  # daily, weekly, monthly
    topics = Column(JSON, nullable=True)  # Array of interested topics
    
    # Tracking
    confirmation_token = Column(String(64), unique=True, nullable=True)
    unsubscribe_token = Column(String(64), unique=True, nullable=True)
    
    # Technical info
    ip_address = Column(INET, nullable=True)
    user_agent = Column(String(1000), nullable=True)
    referrer = Column(String(500), nullable=True)
    source = Column(String(100), nullable=True)  # Where they subscribed from
    
    def confirm_subscription(self):
        """Confirm newsletter subscription"""
        self.is_confirmed = True
        self.confirmed_at = datetime.utcnow()
        self.confirmation_token = None
    
    def unsubscribe(self):
        """Unsubscribe from newsletter"""
        self.is_active = False
        self.unsubscribed_at = datetime.utcnow()
    
    def __repr__(self):
        return f"<NewsletterSubscriber(email={self.email}, active={self.is_active})>"