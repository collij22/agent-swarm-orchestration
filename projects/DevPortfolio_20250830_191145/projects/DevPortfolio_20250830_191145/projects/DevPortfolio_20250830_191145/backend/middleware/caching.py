"""
High-Performance Caching Middleware
Implements multi-layer caching for <200ms API responses
"""

import json
import hashlib
from typing import Optional, Any, Dict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis
from datetime import timedelta
import logging
import time

logger = logging.getLogger(__name__)

class CachingMiddleware(BaseHTTPMiddleware):
    """
    Advanced caching middleware with multiple cache layers:
    - Redis for API responses
    - Memory cache for frequent data
    - CDN headers for static content
    """
    
    def __init__(self, app, redis_url: str = "redis://localhost:6379/0"):
        super().__init__(app)
        self.redis_url = redis_url
        self.redis_client = None
        
        # Cache configuration by endpoint pattern
        self.cache_config = {
            # Blog content - cache for 5 minutes
            r"/api/blog/posts": {"ttl": 300, "vary_by": ["page", "limit", "tag"]},
            r"/api/blog/posts/\w+": {"ttl": 900, "vary_by": []},  # Individual posts - 15 min
            
            # Portfolio - cache for 10 minutes
            r"/api/portfolio/projects": {"ttl": 600, "vary_by": ["featured", "tech"]},
            r"/api/portfolio/skills": {"ttl": 1800, "vary_by": []},  # Skills - 30 min
            r"/api/portfolio/experience": {"ttl": 1800, "vary_by": []},  # Experience - 30 min
            
            # Analytics - cache for 1 minute (fresher data)
            r"/api/analytics/stats": {"ttl": 60, "vary_by": ["period"]},
            
            # AI assistant responses - cache for 1 hour (expensive calls)
            r"/api/ai/suggestions": {"ttl": 3600, "vary_by": ["content_hash"]},
            
            # GitHub data - cache for 15 minutes
            r"/api/github/repos": {"ttl": 900, "vary_by": []},
            r"/api/github/stats": {"ttl": 900, "vary_by": []},
        }
        
        # Memory cache for ultra-fast access
        self.memory_cache: Dict[str, Dict] = {}
        self.memory_cache_ttl = 60  # 1 minute memory cache
    
    async def get_redis_client(self):
        """Get Redis client with connection pooling"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=2,
                socket_connect_timeout=2,
                retry_on_timeout=True,
                max_connections=20,
            )
        return self.redis_client
    
    def generate_cache_key(self, request: Request, config: Dict) -> str:
        """Generate cache key based on request and configuration"""
        key_parts = [request.url.path]
        
        # Add query parameters that affect caching
        for param in config.get("vary_by", []):
            value = request.query_params.get(param)
            if value:
                key_parts.append(f"{param}:{value}")
        
        # Add user context for personalized content
        user_id = request.headers.get("x-user-id")
        if user_id:
            key_parts.append(f"user:{user_id}")
        
        # Create hash for consistent key length
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_cache_config(self, path: str) -> Optional[Dict]:
        """Get cache configuration for request path"""
        import re
        for pattern, config in self.cache_config.items():
            if re.match(pattern, path):
                return config
        return None
    
    async def get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Get response from cache (memory first, then Redis)"""
        # Check memory cache first
        if cache_key in self.memory_cache:
            cached = self.memory_cache[cache_key]
            if time.time() - cached["timestamp"] < self.memory_cache_ttl:
                logger.debug(f"Memory cache hit: {cache_key}")
                return cached["data"]
            else:
                # Expired, remove from memory cache
                del self.memory_cache[cache_key]
        
        # Check Redis cache
        try:
            redis_client = await self.get_redis_client()
            cached_data = await redis_client.get(f"api_cache:{cache_key}")
            if cached_data:
                logger.debug(f"Redis cache hit: {cache_key}")
                data = json.loads(cached_data)
                
                # Store in memory cache for ultra-fast access
                self.memory_cache[cache_key] = {
                    "data": data,
                    "timestamp": time.time()
                }
                
                return data
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
        
        return None
    
    async def set_cached_response(self, cache_key: str, data: Dict, ttl: int):
        """Store response in cache"""
        try:
            # Store in Redis
            redis_client = await self.get_redis_client()
            await redis_client.setex(
                f"api_cache:{cache_key}",
                ttl,
                json.dumps(data, default=str)
            )
            
            # Store in memory cache
            self.memory_cache[cache_key] = {
                "data": data,
                "timestamp": time.time()
            }
            
            logger.debug(f"Cached response: {cache_key} (TTL: {ttl}s)")
            
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")
    
    async def dispatch(self, request: Request, call_next):
        """Process request with caching"""
        start_time = time.time()
        
        # Only cache GET requests
        if request.method != "GET":
            response = await call_next(request)
            return response
        
        # Check if endpoint should be cached
        cache_config = self.get_cache_config(request.url.path)
        if not cache_config:
            response = await call_next(request)
            return response
        
        # Generate cache key
        cache_key = self.generate_cache_key(request, cache_config)
        
        # Try to get cached response
        cached_response = await self.get_cached_response(cache_key)
        if cached_response:
            # Return cached response
            response = Response(
                content=json.dumps(cached_response["body"]),
                status_code=cached_response["status_code"],
                headers=cached_response["headers"]
            )
            response.headers["X-Cache"] = "HIT"
            response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
            return response
        
        # Process request
        response = await call_next(request)
        
        # Cache successful responses
        if 200 <= response.status_code < 300:
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Prepare cache data
            cache_data = {
                "body": json.loads(body.decode()) if body else {},
                "status_code": response.status_code,
                "headers": dict(response.headers)
            }
            
            # Store in cache
            await self.set_cached_response(
                cache_key, 
                cache_data, 
                cache_config["ttl"]
            )
            
            # Create new response
            response = Response(
                content=body,
                status_code=response.status_code,
                headers=response.headers
            )
        
        # Add performance headers
        response.headers["X-Cache"] = "MISS"
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        
        # Add CDN cache headers for static content
        if "static" in request.url.path or request.url.path.endswith(('.js', '.css', '.png', '.jpg', '.svg')):
            response.headers["Cache-Control"] = "public, max-age=31536000"  # 1 year
            response.headers["ETag"] = hashlib.md5(str(response.body).encode()).hexdigest()
        
        return response


class ExternalAPICache:
    """
    Specialized cache for external API calls (GitHub, OpenAI, etc.)
    Implements aggressive caching to reduce external API costs and latency
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        self.redis_url = redis_url
        self.redis_client = None
        
        # Cache TTL for different external APIs
        self.api_cache_ttl = {
            "github": 900,  # 15 minutes
            "openai": 3600,  # 1 hour (expensive calls)
            "oauth": 300,   # 5 minutes
            "analytics": 60,  # 1 minute
        }
    
    async def get_redis_client(self):
        """Get Redis client for external API cache"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                max_connections=10,
            )
        return self.redis_client
    
    async def get(self, api_type: str, cache_key: str) -> Optional[Any]:
        """Get cached external API response"""
        try:
            redis_client = await self.get_redis_client()
            cached_data = await redis_client.get(f"external_api:{api_type}:{cache_key}")
            if cached_data:
                logger.debug(f"External API cache hit: {api_type}:{cache_key}")
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"External API cache retrieval error: {e}")
        return None
    
    async def set(self, api_type: str, cache_key: str, data: Any):
        """Cache external API response"""
        try:
            redis_client = await self.get_redis_client()
            ttl = self.api_cache_ttl.get(api_type, 300)
            await redis_client.setex(
                f"external_api:{api_type}:{cache_key}",
                ttl,
                json.dumps(data, default=str)
            )
            logger.debug(f"Cached external API response: {api_type}:{cache_key}")
        except Exception as e:
            logger.warning(f"External API cache storage error: {e}")

# Global cache instance
external_api_cache = ExternalAPICache()