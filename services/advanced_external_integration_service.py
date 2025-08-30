import os
import logging
from typing import Dict, Any, Optional
from functools import wraps
import requests
import backoff
import jwt
from cryptography.fernet import Fernet

class AdvancedExternalIntegrationService:
    def __init__(self, config_path: str = 'config/external_services.json'):
        """
        Initialize the advanced external integration service
        Manages multiple external service integrations with advanced features
        """
        self.logger = logging.getLogger('external_integration')
        self.config = self._load_config(config_path)
        self._encryption_key = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
        self._encryptor = Fernet(self._encryption_key)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load and validate external services configuration
        """
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise

    def secure_api_call(self, service_name: str, method: str, endpoint: str, **kwargs):
        """
        Secure API call wrapper with advanced error handling and retry logic
        
        :param service_name: Name of the external service
        :param method: HTTP method (get, post, etc.)
        :param endpoint: API endpoint
        :param kwargs: Additional request parameters
        :return: API response
        """
        @backoff.on_exception(
            backoff.expo, 
            (requests.RequestException, ValueError), 
            max_tries=3
        )
        def _call():
            service_config = self.config.get(service_name, {})
            headers = kwargs.get('headers', {})
            headers['Authorization'] = self._get_secure_token(service_name)
            
            try:
                response = getattr(requests, method.lower())(
                    f"{service_config['base_url']}{endpoint}",
                    headers=headers,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                self.logger.error(f"API call failed: {e}")
                raise

        return _call()

    def _get_secure_token(self, service_name: str) -> str:
        """
        Retrieve and decrypt secure API tokens
        
        :param service_name: Name of the service
        :return: Decrypted API token
        """
        encrypted_token = os.environ.get(f"{service_name.upper()}_TOKEN")
        if not encrypted_token:
            raise ValueError(f"No token found for {service_name}")
        
        try:
            decrypted_token = self._encryptor.decrypt(encrypted_token.encode()).decode()
            return f"Bearer {decrypted_token}"
        except Exception as e:
            self.logger.error(f"Token decryption failed: {e}")
            raise

    def validate_webhook(self, service_name: str, payload: Dict[str, Any], signature: str) -> bool:
        """
        Validate webhook signatures with advanced security checks
        
        :param service_name: Name of the service
        :param payload: Webhook payload
        :param signature: Signature to validate
        :return: Validation result
        """
        service_config = self.config.get(service_name, {})
        secret = service_config.get('webhook_secret')
        
        if not secret:
            self.logger.warning(f"No webhook secret for {service_name}")
            return False
        
        try:
            # Implement service-specific signature validation
            # Example: GitHub-style HMAC SHA256 validation
            import hmac
            import hashlib
            
            computed_signature = hmac.new(
                secret.encode(), 
                payload.encode(), 
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(computed_signature, signature)
        except Exception as e:
            self.logger.error(f"Webhook validation failed: {e}")
            return False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('external_integration.log')
    ]
)