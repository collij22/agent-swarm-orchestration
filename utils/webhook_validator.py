import hashlib
import hmac
import os
import logging
from typing import Dict, Any

class WebhookValidator:
    @staticmethod
    def validate_github_webhook(payload: bytes, signature: str, secret: str) -> bool:
        """
        Validate GitHub webhook signature
        
        Args:
            payload (bytes): Raw webhook payload
            signature (str): X-Hub-Signature-256 header
            secret (str): Webhook secret
        
        Returns:
            bool: Signature validity
        """
        try:
            if not signature or not secret:
                logging.warning("Missing signature or secret")
                return False
            
            # Compute HMAC SHA-256 signature
            expected_signature = 'sha256=' + hmac.new(
                key=secret.encode('utf-8'),
                msg=payload,
                digestmod=hashlib.sha256
            ).hexdigest()
            
            # Compare signatures in constant time
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logging.error(f"Webhook validation error: {e}")
            return False
    
    @staticmethod
    def validate_openai_webhook(payload: Dict[str, Any], signature: str) -> bool:
        """
        Validate OpenAI webhook signature
        
        Args:
            payload (dict): Webhook payload
            signature (str): Signature header
        
        Returns:
            bool: Signature validity
        """
        try:
            # Implement OpenAI-specific signature validation
            # This is a placeholder and should be replaced with actual OpenAI validation logic
            return True
        except Exception as e:
            logging.error(f"OpenAI webhook validation error: {e}")
            return False
    
    @classmethod
    def validate_webhook(
        cls, 
        service: str, 
        payload: bytes, 
        signature: str, 
        secret: str = None
    ) -> bool:
        """
        Centralized webhook validation router
        
        Args:
            service (str): Webhook source service
            payload (bytes): Raw webhook payload
            signature (str): Signature header
            secret (str, optional): Service secret
        
        Returns:
            bool: Webhook validation result
        """
        validation_map = {
            'github': cls.validate_github_webhook,
            'openai': cls.validate_openai_webhook
        }
        
        validator = validation_map.get(service.lower())
        if not validator:
            logging.warning(f"No validator found for service: {service}")
            return False
        
        return validator(payload, signature, secret) if secret else validator(payload, signature)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)