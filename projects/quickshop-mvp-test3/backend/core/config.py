from pydantic import BaseSettings, SecretStr

class Settings(BaseSettings):
    # Stripe Configuration
    STRIPE_SECRET_KEY: SecretStr
    STRIPE_PUBLISHABLE_KEY: SecretStr
    STRIPE_WEBHOOK_SECRET: SecretStr

    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: SecretStr
    AWS_SECRET_ACCESS_KEY: SecretStr
    AWS_S3_BUCKET_NAME: str

    # SendGrid Configuration
    SENDGRID_API_KEY: SecretStr

    # Additional environment-specific settings
    DEBUG: bool = False
    ENVIRONMENT: str = 'development'

    class Config:
        # Load environment variables from .env file
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()