import os
from typing import Optional
from dotenv import load_dotenv

class EnvManager:
    """
    Secure environment variable management with validation and default configurations
    """
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize environment configuration
        
        Args:
            env_file (Optional[str]): Path to .env file, defaults to .env in project root
        """
        load_dotenv(env_file or '.env')

    def get_openai_api_key(self) -> str:
        """
        Retrieve OpenAI API key with strict validation
        
        Returns:
            str: Validated OpenAI API key
        
        Raises:
            ValueError: If API key is not configured
        """
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key is not configured. Please set OPENAI_API_KEY in .env")
        
        # Basic validation of API key format
        if not api_key.startswith('sk-'):
            raise ValueError("Invalid OpenAI API key format")
        
        return api_key

    def get_jwt_secret(self) -> str:
        """
        Retrieve JWT secret with strict validation
        
        Returns:
            str: Validated JWT secret
        
        Raises:
            ValueError: If JWT secret is not configured
        """
        jwt_secret = os.getenv('JWT_SECRET')
        if not jwt_secret or len(jwt_secret) < 32:
            raise ValueError("JWT secret must be at least 32 characters long")
        
        return jwt_secret

    def get_database_url(self) -> str:
        """
        Retrieve database connection URL
        
        Returns:
            str: Database connection URL
        """
        db_url = os.getenv('DATABASE_URL', 'sqlite:///tasks.db')
        return db_url

# Singleton instance for easy access
env_manager = EnvManager()