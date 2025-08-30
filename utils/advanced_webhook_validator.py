import hmac
import hashlib
import time
import logging
from typing import Dict, Any, Optional
from functools import wraps

class WebhookValidator:
    def __init__(self, secret_key: str, tolerance_seconds: int = 300):
        """
        Initialize webhook validator with secret key and time tolerance
        
        :param secret_key: Webhook signature secret
        :param tolerance_seconds: Time window for webhook validity
        """
        self._secret_key = secret_key
        self._tolerance = tolerance_seconds
        self._logger = logging.getLogger(__name__)

    def validate_signature(self, payload: bytes, signature: str) -> bool:
        """
        Validate webhook signature with advanced checks
        
        :param payload: Raw request payload
        :param signature: Received signature header
        :return: Signature validity
        """
        try:
            # Constant-time comparison to prevent timing attacks
            expected_signature = hmac.new(
                key=self._secret_key.encode('utf-8'),
                msg=payload,
                digestmod=hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(expected_signature, signature):
                self._logger.warning("Signature mismatch detected")
                return False

            return True
        except Exception as e:
            self._logger.error(f"Signature validation error: {e}")
            return False

    def validate_timestamp(self, timestamp: int) -> bool:
        """
        Check webhook timestamp to prevent replay attacks
        
        :param timestamp: Webhook timestamp
        :return: Timestamp validity
        """
        current_time = int(time.time())
        return abs(current_time - timestamp) <= self._tolerance

    def webhook_required(self, func):
        """
        Decorator for webhook validation
        
        :param func: Function to decorate
        :return: Wrapped function with validation
        """
        @wraps(func)
        def wrapper(payload: bytes, signature: str, timestamp: int, *args, **kwargs):
            if not self.validate_signature(payload, signature):
                raise ValueError("Invalid webhook signature")
            
            if not self.validate_timestamp(timestamp):
                raise ValueError("Webhook timestamp expired")
            
            return func(payload, signature, timestamp, *args, **kwargs)
        return wrapper

def get_webhook_validator(service_name: str) -> WebhookValidator:
    """
    Factory method to create webhook validators for different services
    
    :param service_name: Name of the service
    :return: Configured WebhookValidator
    """
    # In production, fetch secrets from secure configuration management
    service_secrets = {
        "github": "github_webhook_secret",
        "openai": "openai_webhook_secret"
    }
    secret = service_secrets.get(service_name)
    
    if not secret:
        raise ValueError(f"No webhook secret found for {service_name}")
    
    return WebhookValidator(secret)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)