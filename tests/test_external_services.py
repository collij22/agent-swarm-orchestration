"""
Unit tests for external integration services
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.external_integration_service import ExternalIntegrationService
from utils.webhook_validator import WebhookValidator
from utils.advanced_webhook_validator import AdvancedWebhookValidator

class TestExternalIntegrationService:
    """Test external integration service"""
    
    def setup_method(self):
        """Setup test instance"""
        self.service = ExternalIntegrationService()
    
    @patch('services.external_integration_service.requests.get')
    def test_github_api_connection(self, mock_get):
        """Test GitHub API connection"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "login": "testuser",
            "public_repos": 42,
            "followers": 100
        }
        mock_get.return_value = mock_response
        
        result = self.service.get_github_user_info("testuser")
        
        assert result is not None
        assert result["login"] == "testuser"
        assert result["public_repos"] == 42
        mock_get.assert_called_once()

    @patch('services.external_integration_service.requests.get')
    def test_github_api_error_handling(self, mock_get):
        """Test GitHub API error handling"""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Not Found"}
        mock_get.return_value = mock_response
        
        result = self.service.get_github_user_info("nonexistentuser")
        
        assert result is None
        mock_get.assert_called_once()

    @patch('services.external_integration_service.requests.get')
    def test_github_repositories_fetch(self, mock_get):
        """Test fetching GitHub repositories"""
        # Mock repositories response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "name": "awesome-project",
                "description": "An awesome project",
                "html_url": "https://github.com/user/awesome-project",
                "language": "Python",
                "stargazers_count": 42,
                "forks_count": 10
            }
        ]
        mock_get.return_value = mock_response
        
        repos = self.service.get_github_repositories("testuser")
        
        assert len(repos) == 1
        assert repos[0]["name"] == "awesome-project"
        assert repos[0]["language"] == "Python"
        assert repos[0]["stargazers_count"] == 42

    @patch('services.external_integration_service.requests.post')
    def test_openai_api_call(self, mock_post):
        """Test OpenAI API call"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "This is a great blog post about Python!"
                }
            }]
        }
        mock_post.return_value = mock_response
        
        result = self.service.get_ai_writing_assistance("Help me write about Python")
        
        assert result is not None
        assert "Python" in result
        mock_post.assert_called_once()

    @patch('services.external_integration_service.requests.post')
    def test_openai_api_error_handling(self, mock_post):
        """Test OpenAI API error handling"""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 429  # Rate limit exceeded
        mock_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}
        mock_post.return_value = mock_response
        
        result = self.service.get_ai_writing_assistance("Test prompt")
        
        assert result is None
        mock_post.assert_called_once()

    def test_rate_limiting_logic(self):
        """Test rate limiting implementation"""
        # Test that rate limiting prevents excessive calls
        with patch.object(self.service, '_check_rate_limit') as mock_rate_limit:
            mock_rate_limit.return_value = False  # Rate limit exceeded
            
            result = self.service.get_github_user_info("testuser")
            assert result is None
            mock_rate_limit.assert_called_once()

    def test_caching_mechanism(self):
        """Test caching mechanism for API responses"""
        with patch.object(self.service, '_get_cached_response') as mock_cache:
            mock_cache.return_value = {"cached": True, "data": "cached_data"}
            
            result = self.service.get_github_user_info("testuser")
            assert result["cached"] is True
            mock_cache.assert_called_once()

    def test_error_logging(self):
        """Test error logging functionality"""
        with patch('services.external_integration_service.logger') as mock_logger:
            with patch('services.external_integration_service.requests.get') as mock_get:
                mock_get.side_effect = Exception("Network error")
                
                result = self.service.get_github_user_info("testuser")
                
                assert result is None
                mock_logger.error.assert_called()

class TestWebhookValidator:
    """Test webhook validation utilities"""
    
    def setup_method(self):
        """Setup test instance"""
        self.validator = WebhookValidator()
    
    def test_github_webhook_validation(self):
        """Test GitHub webhook signature validation"""
        secret = "test_secret"
        payload = b'{"test": "data"}'
        
        # Generate valid signature
        import hmac
        import hashlib
        signature = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        is_valid = self.validator.validate_github_webhook(payload, signature, secret)
        assert is_valid is True

    def test_github_webhook_invalid_signature(self):
        """Test GitHub webhook with invalid signature"""
        secret = "test_secret"
        payload = b'{"test": "data"}'
        invalid_signature = "sha256=invalid_signature"
        
        is_valid = self.validator.validate_github_webhook(payload, invalid_signature, secret)
        assert is_valid is False

    def test_webhook_payload_parsing(self):
        """Test webhook payload parsing"""
        payload = b'{"action": "opened", "number": 123}'
        
        parsed = self.validator.parse_webhook_payload(payload)
        
        assert parsed is not None
        assert parsed["action"] == "opened"
        assert parsed["number"] == 123

    def test_webhook_malformed_payload(self):
        """Test handling of malformed webhook payload"""
        malformed_payload = b'{"invalid": json}'
        
        parsed = self.validator.parse_webhook_payload(malformed_payload)
        assert parsed is None

class TestAdvancedWebhookValidator:
    """Test advanced webhook validation"""
    
    def setup_method(self):
        """Setup test instance"""
        self.validator = AdvancedWebhookValidator()
    
    def test_timestamp_validation(self):
        """Test webhook timestamp validation"""
        current_time = datetime.now().timestamp()
        
        # Valid timestamp (within tolerance)
        is_valid = self.validator.validate_timestamp(str(int(current_time)))
        assert is_valid is True
        
        # Invalid timestamp (too old)
        old_timestamp = str(int(current_time - 3600))  # 1 hour ago
        is_valid = self.validator.validate_timestamp(old_timestamp)
        assert is_valid is False

    def test_rate_limiting_webhook(self):
        """Test webhook rate limiting"""
        source_ip = "192.168.1.1"
        
        # First few requests should be allowed
        for i in range(5):
            is_allowed = self.validator.check_rate_limit(source_ip)
            assert is_allowed is True
        
        # Excessive requests should be blocked
        with patch.object(self.validator, '_get_request_count') as mock_count:
            mock_count.return_value = 100  # Simulate many requests
            is_allowed = self.validator.check_rate_limit(source_ip)
            assert is_allowed is False

    def test_webhook_source_validation(self):
        """Test webhook source IP validation"""
        # Valid GitHub IP ranges (example)
        github_ip = "192.30.252.1"
        is_valid = self.validator.validate_source_ip(github_ip, "github")
        # This would depend on actual implementation
        
        # Invalid IP
        invalid_ip = "1.2.3.4"
        is_valid = self.validator.validate_source_ip(invalid_ip, "github")
        # Should implement proper IP range checking

    def test_webhook_event_filtering(self):
        """Test webhook event filtering"""
        # Test allowed events
        allowed_event = "push"
        is_allowed = self.validator.is_event_allowed(allowed_event, "github")
        assert is_allowed is True
        
        # Test disallowed events
        disallowed_event = "spam_event"
        is_allowed = self.validator.is_event_allowed(disallowed_event, "github")
        assert is_allowed is False

class TestServiceIntegration:
    """Test service integration scenarios"""
    
    def setup_method(self):
        """Setup test instances"""
        self.service = ExternalIntegrationService()
    
    @patch('services.external_integration_service.requests.get')
    def test_github_to_portfolio_sync(self, mock_get):
        """Test syncing GitHub repositories to portfolio"""
        # Mock GitHub API responses
        repos_response = Mock()
        repos_response.status_code = 200
        repos_response.json.return_value = [
            {
                "name": "portfolio-site",
                "description": "My portfolio website",
                "html_url": "https://github.com/user/portfolio-site",
                "language": "Python",
                "stargazers_count": 15,
                "topics": ["portfolio", "fastapi", "python"]
            }
        ]
        mock_get.return_value = repos_response
        
        repos = self.service.sync_github_repositories("testuser")
        
        assert len(repos) > 0
        assert repos[0]["name"] == "portfolio-site"
        assert "fastapi" in repos[0]["topics"]

    def test_ai_content_enhancement(self):
        """Test AI content enhancement workflow"""
        with patch.object(self.service, 'get_ai_writing_assistance') as mock_ai:
            mock_ai.return_value = "Enhanced content with better SEO and readability"
            
            original_content = "Basic blog post content"
            enhanced = self.service.enhance_blog_content(original_content)
            
            assert enhanced != original_content
            assert "Enhanced" in enhanced
            mock_ai.assert_called_once()

    def test_oauth_token_validation(self):
        """Test OAuth token validation"""
        valid_token = "valid_oauth_token"
        invalid_token = "invalid_token"
        
        with patch.object(self.service, '_validate_oauth_token') as mock_validate:
            mock_validate.return_value = True
            
            is_valid = self.service.validate_github_oauth_token(valid_token)
            assert is_valid is True
            
            mock_validate.return_value = False
            is_valid = self.service.validate_github_oauth_token(invalid_token)
            assert is_valid is False

class TestErrorScenarios:
    """Test error scenarios and edge cases"""
    
    def setup_method(self):
        """Setup test instances"""
        self.service = ExternalIntegrationService()
    
    def test_network_timeout_handling(self):
        """Test network timeout handling"""
        with patch('services.external_integration_service.requests.get') as mock_get:
            mock_get.side_effect = TimeoutError("Request timeout")
            
            result = self.service.get_github_user_info("testuser")
            assert result is None

    def test_api_quota_exceeded(self):
        """Test API quota exceeded handling"""
        with patch('services.external_integration_service.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_response.json.return_value = {"message": "API rate limit exceeded"}
            mock_get.return_value = mock_response
            
            result = self.service.get_github_user_info("testuser")
            assert result is None

    def test_malformed_api_response(self):
        """Test handling of malformed API responses"""
        with patch('services.external_integration_service.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_get.return_value = mock_response
            
            result = self.service.get_github_user_info("testuser")
            assert result is None

    def test_partial_service_failure(self):
        """Test handling when some external services fail"""
        with patch.object(self.service, 'check_github_status') as mock_github:
            with patch.object(self.service, 'check_openai_status') as mock_openai:
                mock_github.return_value = {"status": "error"}
                mock_openai.return_value = {"status": "healthy"}
                
                status = self.service.get_all_services_status()
                
                assert status["github"]["status"] == "error"
                assert status["openai"]["status"] == "healthy"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])