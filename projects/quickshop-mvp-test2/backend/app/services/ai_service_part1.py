"""
AI Service Implementation - Part 1: Core Structure and OpenAI Integration
Comprehensive AI service with categorization, caching, rate limiting, and fallbacks
"""

import os
import json
import hashlib
import time
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
from functools import lru_cache
import redis
from redis.exceptions import RedisError
import openai
from openai import OpenAI, AsyncOpenAI
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel
import tiktoken
from fuzzywuzzy import fuzz
import numpy as np

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Custom exception for AI service errors"""
    pass


class RateLimitError(AIServiceError):
    """Rate limit exceeded error"""
    pass


class TokenLimitError(AIServiceError):
    """Token limit exceeded error"""
    pass


# Prompt Templates
CATEGORIZATION_PROMPT = """You are an expert classifier for an e-commerce platform.
Categorize the given text into one of the provided categories.

Return a JSON object with:
- category: the most appropriate category from the list
- confidence: confidence score between 0 and 1
- reasoning: brief explanation for the categorization (max 50 words)

Be consistent and accurate. Consider context clues and keywords."""

PRIORITIZATION_PROMPT = """You are a task prioritization expert for an e-commerce platform.
Analyze the given tasks and rank them based on the specified criteria.

Criteria weights:
- Urgency: 30%
- Business Impact: 30%
- Effort Required: 20%
- Dependencies: 20%

Return a JSON object with:
- tasks: array of tasks ordered by priority (highest first)
- rationale: explanation of the prioritization logic
- scoring_details: optional breakdown of scores per task"""

ANALYSIS_PROMPT = """You are an expert analyst for e-commerce data.
Perform {analysis_type} analysis on the provided content.

Extract:
1. Key insights and patterns
2. Entities (products, categories, brands, etc.)
3. Sentiment and tone
4. Actionable recommendations

Return structured JSON with relevant fields based on the analysis type."""

SUGGESTION_PROMPT = """You are a recommendation expert for an e-commerce platform.
Generate {count} relevant {suggestion_type} suggestions based on the context.

Consider:
- User preferences and history
- Current trends
- Business objectives
- Relevance and diversity

Return suggestions with explanations."""

GRAMMAR_CHECK_PROMPT = """You are a professional editor.
Check the text for grammar, spelling, and style issues.

Style: {style}
Language: {language}

Return:
- corrected_text: the improved version
- corrections: list of specific corrections made
- style_suggestions: optional style improvements"""


class RateLimiter:
    """Token bucket rate limiter with burst support"""
    
    def __init__(self, max_requests: int = 60, window: int = 60, 
                 max_tokens: int = 100000, token_window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.max_tokens = max_tokens
        self.token_window = token_window
        
        self.requests = deque()
        self.tokens_used = deque()
        self.lock = asyncio.Lock()
    
    async def check_and_update(self, tokens_needed: int = 0) -> Tuple[bool, str]:
        """Check if request is allowed and update counters"""
        async with self.lock:
            now = time.time()
            
            # Clean old entries
            while self.requests and self.requests[0] < now - self.window:
                self.requests.popleft()
            
            while self.tokens_used and self.tokens_used[0][0] < now - self.token_window:
                self.tokens_used.popleft()
            
            # Check request limit
            if len(self.requests) >= self.max_requests:
                return False, f"Rate limit exceeded: {self.max_requests} requests per {self.window}s"
            
            # Check token limit
            current_tokens = sum(t[1] for t in self.tokens_used)
            if current_tokens + tokens_needed > self.max_tokens:
                return False, f"Token limit exceeded: {self.max_tokens} tokens per {self.token_window}s"
            
            # Update counters
            self.requests.append(now)
            if tokens_needed > 0:
                self.tokens_used.append((now, tokens_needed))
            
            return True, "OK"


class SmartCache:
    """Intelligent caching with Redis and file fallback"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None, 
                 default_ttl: int = 3600):
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.file_cache_dir = "cache/ai_service"
        os.makedirs(self.file_cache_dir, exist_ok=True)
        
        # Memory cache for ultra-fast access
        self.memory_cache = {}
        self.memory_cache_size = 1000
        self.memory_cache_ttl = 300  # 5 minutes
    
    def _generate_key(self, operation: str, *args, **kwargs) -> str:
        """Generate deterministic cache key"""
        key_data = f"{operation}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get from cache with fallback chain: memory -> Redis -> file"""
        # Check memory cache
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if entry['expires'] > time.time():
                logger.debug(f"Memory cache hit for {key}")
                return entry['data']
            else:
                del self.memory_cache[key]
        
        # Check Redis
        if self.redis:
            try:
                cached = await asyncio.to_thread(self.redis.get, f"ai:{key}")
                if cached:
                    logger.debug(f"Redis cache hit for {key}")
                    data = json.loads(cached)
                    # Update memory cache
                    self._update_memory_cache(key, data)
                    return data
            except RedisError as e:
                logger.warning(f"Redis error: {e}")
        
        # Check file cache
        file_path = os.path.join(self.file_cache_dir, f"{key}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    cache_entry = json.load(f)
                    if cache_entry['expires'] > time.time():
                        logger.debug(f"File cache hit for {key}")
                        return cache_entry['data']
                    else:
                        os.remove(file_path)
            except Exception as e:
                logger.warning(f"File cache error: {e}")
        
        return None
    
    async def set(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None):
        """Set in cache with multi-level storage"""
        ttl = ttl or self.default_ttl
        
        # Update memory cache
        self._update_memory_cache(key, data, ttl=min(ttl, self.memory_cache_ttl))
        
        # Update Redis
        if self.redis:
            try:
                await asyncio.to_thread(
                    self.redis.setex,
                    f"ai:{key}",
                    ttl,
                    json.dumps(data)
                )
            except RedisError as e:
                logger.warning(f"Redis set error: {e}")
        
        # Update file cache
        try:
            file_path = os.path.join(self.file_cache_dir, f"{key}.json")
            cache_entry = {
                'data': data,
                'expires': time.time() + ttl,
                'created': time.time()
            }
            with open(file_path, 'w') as f:
                json.dump(cache_entry, f)
        except Exception as e:
            logger.warning(f"File cache set error: {e}")
    
    def _update_memory_cache(self, key: str, data: Dict[str, Any], ttl: int = None):
        """Update memory cache with LRU eviction"""
        ttl = ttl or self.memory_cache_ttl
        
        # Evict oldest entries if cache is full
        if len(self.memory_cache) >= self.memory_cache_size:
            oldest_key = min(self.memory_cache.keys(), 
                           key=lambda k: self.memory_cache[k]['created'])
            del self.memory_cache[oldest_key]
        
        self.memory_cache[key] = {
            'data': data,
            'expires': time.time() + ttl,
            'created': time.time()
        }


class FallbackProvider:
    """Fallback AI provider for when primary services are unavailable"""
    
    def __init__(self):
        self.keyword_weights = self._load_keyword_weights()
    
    def _load_keyword_weights(self) -> Dict[str, Dict[str, float]]:
        """Load pre-computed keyword weights for categories"""
        # In production, load from file or database
        return {
            "electronics": {
                "phone": 0.9, "laptop": 0.9, "computer": 0.8,
                "tablet": 0.8, "gadget": 0.7, "device": 0.6
            },
            "clothing": {
                "shirt": 0.9, "dress": 0.9, "pants": 0.8,
                "shoes": 0.8, "fashion": 0.7, "wear": 0.6
            },
            "home": {
                "furniture": 0.9, "decor": 0.8, "kitchen": 0.8,
                "bedroom": 0.7, "living": 0.6, "house": 0.5
            },
            "books": {
                "book": 0.9, "novel": 0.8, "read": 0.7,
                "author": 0.7, "story": 0.6, "literature": 0.8
            }
        }
    
    async def categorize(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Keyword-based categorization fallback"""
        text_lower = text.lower()
        scores = {}
        
        for category in categories:
            score = 0.0
            category_lower = category.lower()
            
            # Direct match
            if category_lower in text_lower:
                score += 0.5
            
            # Fuzzy match
            score += fuzz.partial_ratio(category_lower, text_lower) / 200
            
            # Keyword matching
            if category_lower in self.keyword_weights:
                keywords = self.keyword_weights[category_lower]
                for keyword, weight in keywords.items():
                    if keyword in text_lower:
                        score += weight * 0.3
            
            scores[category] = min(score, 1.0)
        
        best_category = max(scores, key=scores.get)
        confidence = scores[best_category]
        
        return {
            "category": best_category,
            "confidence": confidence,
            "reasoning": f"Fallback: keyword matching (confidence: {confidence:.2f})",
            "fallback": True,
            "scores": scores
        }
    
    async def prioritize(self, tasks: List[Dict[str, Any]], 
                        criteria: List[str]) -> Dict[str, Any]:
        """Simple rule-based prioritization"""
        scored_tasks = []
        
        for task in tasks:
            score = 0.0
            
            # Urgency keywords
            if any(word in str(task).lower() for word in 
                   ["urgent", "asap", "critical", "emergency"]):
                score += 0.3
            
            # Importance keywords
            if any(word in str(task).lower() for word in 
                   ["important", "key", "crucial", "vital"]):
                score += 0.3
            
            # Quick wins (low effort)
            if any(word in str(task).lower() for word in 
                   ["quick", "easy", "simple", "minor"]):
                score += 0.2
            
            # Dependencies
            if "blocked" not in str(task).lower():
                score += 0.2
            
            scored_tasks.append({
                **task,
                "_score": score
            })
        
        # Sort by score
        scored_tasks.sort(key=lambda x: x["_score"], reverse=True)
        
        # Remove internal score
        for task in scored_tasks:
            task.pop("_score", None)
        
        return {
            "tasks": scored_tasks,
            "rationale": "Fallback: rule-based prioritization using keyword analysis",
            "fallback": True
        }
    
    async def mock_response(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Generate mock responses for testing"""
        mock_responses = {
            "categorize": {
                "category": "general",
                "confidence": 0.7,
                "reasoning": "Mock response for testing",
                "fallback": True,
                "mock": True
            },
            "prioritize": {
                "tasks": kwargs.get("tasks", []),
                "rationale": "Mock prioritization for testing",
                "fallback": True,
                "mock": True
            },
            "analyze": {
                "summary": "Mock analysis summary",
                "entities": [{"type": "mock", "value": "test"}],
                "sentiment": {"positive": 0.5, "neutral": 0.5, "negative": 0.0},
                "key_points": ["Mock key point 1", "Mock key point 2"],
                "fallback": True,
                "mock": True
            }
        }
        
        return mock_responses.get(operation, {
            "error": "Unknown operation",
            "fallback": True,
            "mock": True
        })