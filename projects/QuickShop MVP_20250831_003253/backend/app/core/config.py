from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://quickshop:quickshop123@localhost:5432/quickshop"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production-make-it-very-long-and-random"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    # SendGrid
    SENDGRID_API_KEY: Optional[str] = None
    FROM_EMAIL: str = "noreply@quickshop.com"
    
    # AWS S3 (for file uploads)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_BUCKET_NAME: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    
    # Application
    DEBUG: bool = True
    PROJECT_NAME: str = "QuickShop MVP"
    VERSION: str = "1.0.0"
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()