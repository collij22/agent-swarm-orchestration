from pydantic import BaseSettings
import os

class Settings(BaseSettings):
    # Stripe Configuration
    STRIPE_SECRET_KEY: str = os.getenv('STRIPE_SECRET_KEY', '')
    STRIPE_WEBHOOK_SECRET: str = os.getenv('STRIPE_WEBHOOK_SECRET', '')
    
    # SendGrid Configuration
    SENDGRID_API_KEY: str = os.getenv('SENDGRID_API_KEY', '')
    SENDGRID_FROM_EMAIL: str = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@quickshop.com')
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: str = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY: str = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    AWS_S3_BUCKET_NAME: str = os.getenv('AWS_S3_BUCKET_NAME', 'quickshop-product-images')
    AWS_S3_REGION: str = os.getenv('AWS_S3_REGION', 'us-east-1')
    
    # Google Analytics Configuration
    GA_MEASUREMENT_ID: str = os.getenv('GA_MEASUREMENT_ID', '')
    GA_API_SECRET: str = os.getenv('GA_API_SECRET', '')
    
    # Application Settings
    DEBUG: bool = os.getenv('DEBUG', 'False') == 'True'
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')

    class Config:
        # Allow reading from .env file
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create a singleton settings instance
settings = Settings()