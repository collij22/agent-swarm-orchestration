import os
from typing import Dict, Any, Optional
from httpx import AsyncClient, HTTPStatusError, RequestError
import jwt
import time
import logging
from functools import wraps

class IntegrationService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('integration_service')
        self.client = AsyncClient()

    def rate_limit_decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    return await func(self, *args, **kwargs)
                except HTTPStatusError as e:
                    if e.response.status_code == 429:  # Rate limit hit
                        wait_time = 2 ** attempt  # Exponential backoff
                        self.logger.warning(f"Rate limit hit. Waiting {wait_time} seconds.")
                        await asyncio.sleep(wait_time)
                    else:
                        raise
            raise Exception("Max retries exceeded")
        return wrapper

    async def authenticate_github(self) -> str:
        """Authenticate with GitHub API using OAuth2"""
        try:
            # Implement secure GitHub OAuth flow
            token = os.getenv('GITHUB_ACCESS_TOKEN')
            return token
        except Exception as e:
            self.logger.error(f"GitHub authentication failed: {e}")
            raise

    @rate_limit_decorator
    async def fetch_github_repos(self, username: str) -> Dict[str, Any]:
        """Fetch GitHub repositories with rate limiting"""
        try:
            token = await self.authenticate_github()
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = await self.client.get(
                f'https://api.github.com/users/{username}/repos', 
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"GitHub repo fetch failed: {e}")
            raise

    async def generate_openai_content(self, prompt: str) -> str:
        """Generate content using OpenAI with error handling"""
        try:
            openai_key = os.getenv('OPENAI_API_KEY')
            headers = {
                'Authorization': f'Bearer {openai_key}',
                'Content-Type': 'application/json'
            }
            payload = {
                'model': 'gpt-3.5-turbo',
                'messages': [{'role': 'user', 'content': prompt}]
            }
            response = await self.client.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            self.logger.error(f"OpenAI content generation failed: {e}")
            raise

    def create_jwt_token(self, user_id: str, expires_in: int = 3600) -> str:
        """Create a secure JWT token for authentication"""
        try:
            payload = {
                'sub': user_id,
                'iat': time.time(),
                'exp': time.time() + expires_in
            }
            secret = os.getenv('JWT_SECRET')
            return jwt.encode(payload, secret, algorithm='HS256')
        except Exception as e:
            self.logger.error(f"JWT token creation failed: {e}")
            raise

def get_integration_service(config: Dict[str, Any]) -> IntegrationService:
    """Factory method to create integration service"""
    return IntegrationService(config)