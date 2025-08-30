import os
import requests
from typing import Dict, Any, Optional
from fastapi import HTTPException
from dotenv import load_dotenv
import jwt
import openai

load_dotenv()

class APIIntegrationService:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        openai.api_key = self.openai_key

    def get_github_repositories(self, username: str) -> Dict[str, Any]:
        """Fetch GitHub repositories with caching and error handling"""
        try:
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.get(f'https://api.github.com/users/{username}/repos', headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"GitHub API error: {str(e)}")

    def generate_ai_content(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate content using OpenAI with rate limiting"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

    def generate_jwt_token(self, user_id: str, expires_in: int = 3600) -> str:
        """Generate secure JWT token for authentication"""
        payload = {
            'sub': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in)
        }
        return jwt.encode(payload, os.getenv('JWT_SECRET'), algorithm='HS256')

    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            return jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")