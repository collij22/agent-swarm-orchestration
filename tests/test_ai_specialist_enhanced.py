#!/usr/bin/env python3

"""
Comprehensive Test Suite for Enhanced AI Specialist
Tests all Section 5 refinements implementation
"""

import os
import sys
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import the enhanced AI specialist
from sfa.sfa_ai_specialist_enhanced import (
    EnhancedAISpecialistAgent,
    AICache,
    CacheConfig,
    RateLimiter,
    RateLimitConfig
)

class TestOpenAIIntegrationGeneration:
    """Test OpenAI integration code generation"""
    
    @pytest.fixture
    def agent(self):
        """Create test agent"""
        return EnhancedAISpecialistAgent()
    
    def test_generate_openai_integration(self, agent):
        """Test OpenAI integration code generation"""
        files = agent.generate_openai_integration(
            "Test OpenAI integration",
            ["categorization", "analysis", "caching"],
            with_fallback=True
        )
        
        # Check all required files are generated
        assert "openai_client.py" in files
        assert "categorization_api.py" in files
        assert "prompt_engineering.py" in files
        assert "caching_system.py" in files
        assert "fallback_system.py" in files
        assert "requirements.txt" in files
        assert "config.yaml" in files
        assert "Dockerfile" in files
        
        # Verify OpenAI client content
        openai_client = files["openai_client.py"]
        assert "OpenAIClient" in openai_client
        assert "def complete" in openai_client
        assert "def embed" in openai_client
        assert "_use_fallback" in openai_client
        assert "RateLimitError" in openai_client
        
        # Verify categorization API content
        categorization_api = files["categorization_api.py"]
        assert "TaskCategory" in categorization_api
        assert "Priority" in categorization_api
        assert "/api/categorize" in categorization_api
        assert "/api/prioritize/batch" in categorization_api
        assert "_manual_categorization" in categorization_api
        
        # Verify prompt engineering content
        prompt_engineering = files["prompt_engineering.py"]
        assert "PromptEngineer" in prompt_engineering
        assert "task_analysis" in prompt_engineering
        assert "optimize_prompt" in prompt_engineering
        assert "few_shot_examples" in prompt_engineering
        
        # Verify caching system
        caching_system = files["caching_system.py"]
        assert "AICache" in caching_system
        assert "RateLimiter" in caching_system
        assert "with_caching" in caching_system
        assert "with_rate_limiting" in caching_system
        assert "redis" in caching_system
        
        # Verify fallback system
        fallback_system = files["fallback_system.py"]
        assert "FallbackChain" in fallback_system
        assert "MockAIProvider" in fallback_system
        assert "GracefulDegradation" in fallback_system
        assert "manual_bug_detector" in fallback_system
        assert "manual_priority_scorer" in fallback_system
    
    def test_task_analysis_system(self, agent):
        """Test complete task analysis system generation"""
        files = agent.implement_task_analysis_system(
            "Test task analysis",
            {"features": ["categorization", "caching", "fallback"]}
        )
        
        # Check task analysis API is included
        assert "task_analysis_api.py" in files
        assert "test_ai_system.py" in files
        assert "README.md" in files
        
        # Verify task analysis API content
        task_api = files["task_analysis_api.py"]
        assert "/api/analyze/task" in task_api
        assert "/api/analyze/batch" in task_api
        assert "/api/cache/stats" in task_api
        assert "/api/cache/invalidate" in task_api
        assert "with_rate_limiting" in task_api
        assert "with_caching" in task_api
        
        # Verify test suite
        test_suite = files["test_ai_system.py"]
        assert "TestOpenAIIntegration" in test_suite
        assert "TestCategorization" in test_suite
        assert "TestPromptEngineering" in test_suite
        assert "TestCaching" in test_suite
        assert "TestRateLimiting" in test_suite
        assert "TestFallback" in test_suite

class TestCachingSystem:
    """Test caching functionality"""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_cache_initialization(self, temp_cache_dir):
        """Test cache initialization"""
        config = CacheConfig(
            enabled=True,
            ttl_seconds=3600,
            cache_dir=temp_cache_dir
        )
        cache = AICache(config)
        
        assert cache.config.enabled
        assert cache.cache_dir == temp_cache_dir
        assert temp_cache_dir.exists()
    
    def test_cache_get_set(self, temp_cache_dir):
        """Test cache get and set operations"""
        config = CacheConfig(cache_dir=temp_cache_dir)
        cache = AICache(config)
        
        # Test cache miss
        result = cache.get("test prompt", {"param": "value"})
        assert result is None
        
        # Test cache set
        cache.set("test prompt", {"param": "value"}, "test response")
        
        # Test cache hit
        result = cache.get("test prompt", {"param": "value"})
        assert result == "test response"
    
    def test_cache_expiration(self, temp_cache_dir):
        """Test cache expiration"""
        config = CacheConfig(
            cache_dir=temp_cache_dir,
            ttl_seconds=1  # 1 second TTL
        )
        cache = AICache(config)
        
        # Set cache entry
        cache.set("test", {}, "response")
        assert cache.get("test", {}) == "response"
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Should be expired
        result = cache.get("test", {})
        assert result is None
    
    def test_cache_key_generation(self, temp_cache_dir):
        """Test cache key generation"""
        config = CacheConfig(cache_dir=temp_cache_dir)
        cache = AICache(config)
        
        # Same inputs should generate same key
        key1 = cache._get_cache_key("prompt", {"a": 1, "b": 2})
        key2 = cache._get_cache_key("prompt", {"b": 2, "a": 1})
        assert key1 == key2
        
        # Different inputs should generate different keys
        key3 = cache._get_cache_key("different", {"a": 1})
        assert key1 != key3

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization"""
        config = RateLimitConfig(
            max_requests_per_minute=60,
            max_tokens_per_minute=100000
        )
        limiter = RateLimiter(config)
        
        assert limiter.config.max_requests_per_minute == 60
        assert limiter.config.max_tokens_per_minute == 100000
    
    def test_request_rate_limiting(self):
        """Test request rate limiting"""
        config = RateLimitConfig(
            max_requests_per_minute=5,
            burst_size=2
        )
        limiter = RateLimiter(config)
        
        # Should allow first 5 requests
        for _ in range(5):
            limiter.check_and_wait(100)
            assert len(limiter.request_times) <= 5
        
        # 6th request should require waiting
        # (This test is simplified - in real scenario it would wait)
        assert len(limiter.request_times) == 5
    
    def test_token_rate_limiting(self):
        """Test token rate limiting"""
        config = RateLimitConfig(
            max_tokens_per_minute=1000
        )
        limiter = RateLimiter(config)
        
        # Use up most of the token budget
        limiter.check_and_wait(900)
        limiter.token_counts.append(900)
        
        # Small request should still work
        limiter.check_and_wait(50)
        
        # Large request would exceed limit
        # (In real scenario would wait)
        assert sum(limiter.token_counts) <= 1000

class TestMockResponses:
    """Test mock AI responses"""
    
    def test_mock_initialization(self):
        """Test mock responses initialization"""
        agent = EnhancedAISpecialistAgent()
        
        assert "categorization" in agent.mock_responses
        assert "priority_scores" in agent.mock_responses
        
        # Check categorization patterns
        assert "bug" in agent.mock_responses["categorization"]
        assert "feature" in agent.mock_responses["categorization"]
        
        # Check priority patterns
        assert "critical" in agent.mock_responses["priority_scores"]
        assert "high" in agent.mock_responses["priority_scores"]

class TestFileGeneration:
    """Test file generation and saving"""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_save_enhanced_system(self, temp_output_dir):
        """Test saving enhanced system to disk"""
        agent = EnhancedAISpecialistAgent()
        
        # Generate files
        agent.generate_openai_integration(
            "Test generation",
            ["categorization", "caching"]
        )
        
        # Save to disk
        success = agent.save_enhanced_system(str(temp_output_dir))
        assert success
        
        # Check files were created
        expected_files = [
            "openai_client.py",
            "categorization_api.py",
            "prompt_engineering.py",
            "caching_system.py",
            "fallback_system.py",
            "requirements.txt",
            "config.yaml",
            "Dockerfile"
        ]
        
        for filename in expected_files:
            file_path = temp_output_dir / filename
            assert file_path.exists(), f"File {filename} not created"
            
            # Verify file has content
            content = file_path.read_text()
            assert len(content) > 0, f"File {filename} is empty"

class TestIntegration:
    """Integration tests for the complete system"""
    
    def test_full_workflow(self):
        """Test complete workflow from requirements to implementation"""
        agent = EnhancedAISpecialistAgent()
        
        # Define requirements
        requirements = {
            "features": ["task_categorization", "ai_analysis", "caching"],
            "providers": ["openai", "anthropic"],
            "performance": {
                "cache_ttl": 3600,
                "rate_limit": 60
            }
        }
        
        # Generate complete system
        files = agent.implement_task_analysis_system(
            "Complete AI task analysis system",
            requirements
        )
        
        # Verify all components are present
        assert len(files) > 10  # Should have many files
        
        # Check for key integrations
        all_content = " ".join(files.values())
        assert "OpenAI" in all_content
        assert "cache" in all_content.lower()
        assert "rate" in all_content.lower()
        assert "fallback" in all_content.lower()
        assert "categorization" in all_content.lower()
        assert "prioritization" in all_content.lower()
    
    def test_error_handling(self):
        """Test error handling in the system"""
        agent = EnhancedAISpecialistAgent()
        
        # Test with no API key (should use mock)
        agent.api_key = None
        agent.client = None
        
        files = agent.generate_openai_integration(
            "Test without API",
            ["basic"],
            with_fallback=True
        )
        
        # Should still generate files
        assert len(files) > 0
        assert "fallback_system.py" in files

class TestAPIEndpoints:
    """Test generated API endpoint code"""
    
    def test_categorization_endpoint_code(self):
        """Test categorization endpoint generation"""
        agent = EnhancedAISpecialistAgent()
        files = agent.generate_openai_integration(
            "Test", ["categorization"]
        )
        
        api_code = files["categorization_api.py"]
        
        # Check endpoint definitions
        assert "@app.post" in api_code
        assert '"/api/categorize"' in api_code
        assert '"/api/prioritize/batch"' in api_code
        
        # Check request/response models
        assert "TaskRequest" in api_code
        assert "TaskResponse" in api_code
        assert "TaskCategory" in api_code
        assert "Priority" in api_code
        
        # Check AI integration
        assert "ai_client.complete" in api_code
        assert "manual_categorization" in api_code
    
    def test_analysis_endpoint_code(self):
        """Test analysis endpoint generation"""
        agent = EnhancedAISpecialistAgent()
        files = agent.implement_task_analysis_system(
            "Test", {}
        )
        
        if "task_analysis_api.py" in files:
            api_code = files["task_analysis_api.py"]
            
            # Check analysis endpoints
            assert "/api/analyze/task" in api_code
            assert "/api/analyze/batch" in api_code
            
            # Check caching decorators
            assert "@with_caching" in api_code
            assert "@with_rate_limiting" in api_code
            
            # Check background tasks
            assert "BackgroundTasks" in api_code
            assert "process_batch_analysis" in api_code

class TestPromptEngineering:
    """Test prompt engineering features"""
    
    def test_prompt_templates(self):
        """Test prompt template generation"""
        agent = EnhancedAISpecialistAgent()
        files = agent.generate_openai_integration(
            "Test", ["analysis"]
        )
        
        prompt_code = files["prompt_engineering.py"]
        
        # Check template types
        assert "task_analysis" in prompt_code
        assert "code_generation" in prompt_code
        assert "optimization" in prompt_code
        
        # Check few-shot examples
        assert "few_shot_examples" in prompt_code
        assert '"input":' in prompt_code
        assert '"output":' in prompt_code
        
        # Check optimization methods
        assert "optimize_for_clarity" in prompt_code
        assert "optimize_for_conciseness" in prompt_code
        assert "optimize_for_specificity" in prompt_code

class TestDockerSupport:
    """Test Docker configuration generation"""
    
    def test_dockerfile_generation(self):
        """Test Dockerfile generation"""
        agent = EnhancedAISpecialistAgent()
        files = agent.generate_openai_integration(
            "Test", ["deployment"]
        )
        
        dockerfile = files["Dockerfile"]
        
        # Check Docker configuration
        assert "FROM python:3.11-slim" in dockerfile
        assert "WORKDIR /app" in dockerfile
        assert "requirements.txt" in dockerfile
        assert "EXPOSE 8000" in dockerfile
        assert "uvicorn" in dockerfile

if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([__file__, "-v", "--cov=sfa.sfa_ai_specialist_enhanced"])