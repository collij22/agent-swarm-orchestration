import os
import time
import requests
from typing import Dict, Any, Optional
from functools import wraps

class APIIntegrator:
    """
    Centralized utility for managing external API integrations
    with robust error handling and rate limiting
    """
    
    def __init__(self, config_path: str = '/config/integrations.yml'):
        self.config = self._load_config(config_path)
        self.retry_attempts = 3
        self.backoff_factor = 2

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load integration configuration"""
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def rate_limit_decorator(service_name: str):
        """
        Decorator to implement rate limiting and exponential backoff
        """
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                service_config = self.config.get(service_name, {})
                rate_limit = service_config.get('rate_limit', {})
                
                for attempt in range(self.retry_attempts):
                    try:
                        response = func(self, *args, **kwargs)
                        return response
                    except requests.exceptions.RequestException as e:
                        if attempt == self.retry_attempts - 1:
                            raise
                        
                        # Exponential backoff
                        sleep_time = (self.backoff_factor ** attempt)
                        time.sleep(sleep_time)
                
            return wrapper
        return decorator

    @rate_limit_decorator('github')
    def github_request(self, endpoint: str, method: str = 'GET', 
                       data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Secure GitHub API request with OAuth authentication
        """
        headers = {
            'Authorization': f'token {os.getenv("GITHUB_TOKEN")}',
            'Accept': 'application/vnd.github.v4+json'
        }
        
        response = requests.request(
            method, 
            f'https://api.github.com{endpoint}', 
            headers=headers, 
            json=data
        )
        
        response.raise_for_status()
        return response.json()

    @rate_limit_decorator('openai')
    def openai_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Secure OpenAI API request with error handling
        """
        headers = {
            'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f'https://api.openai.com/v1/{endpoint}',
            headers=headers,
            json=payload
        )
        
        response.raise_for_status()
        return response.json()

    def validate_webhook_signature(self, service: str, payload: bytes, signature: str) -> bool:
        """
        Validate webhook signatures to prevent tampering
        """
        import hmac
        import hashlib

        secret = os.getenv(f'{service.upper()}_WEBHOOK_SECRET')
        if not secret:
            raise ValueError(f"No webhook secret found for {service}")

        expected_signature = hmac.new(
            secret.encode('utf-8'), 
            payload, 
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

# Example usage in other modules
def get_github_projects():
    integrator = APIIntegrator()
    return integrator.github_request('/user/repos')