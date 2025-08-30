"""
High-Performance Redis Caching Service
Comprehensive caching strategy for DevPortfolio API
"""

import redis.asyncio as redis
import json
import pickle
import hashlib
import logging
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import os
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)

class CacheConfig:
    """Cache configuration constants"""
    
    # Cache TTL settings (in seconds)
    TTL_SHORT = 300      # 5 minutes - for frequently changing data
    TTL_MEDIUM = 1800    # 30 minutes - for semi-static data
    TTL_LONG = 3600      # 1 hour - for static data
    TTL_VERY_LONG = 86400  # 24 hours - for rarely changing data
    
    # Cache key prefixes
    PREFIX_PROJECT = "project:"
    PREFIX_BLOG = "blog:"
    PREFIX_USER = "user:"
    PREFIX_ANALYTICS = "analytics:"
    PREFIX_SKILL = "skill:"
    PREFIX_EXPERIENCE = "experience:"
    PREFIX_API = "api:"
    PREFIX_SEARCH = "search:"
    
    # Performance settings
    MAX_CONNECTIONS = 100
    RETRY_ON_TIMEOUT = True
    SOCKET_KEEPALIVE = True

class CacheService:
    """High-performance Redis caching service"""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client: Optional[redis.Redis] = None
        self.connection_pool: Optional[redis.ConnectionPool] = None
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
    
    async def initialize(self):
        """Initialize Redis connection with optimized settings"""
        try:
            # Create optimized connection pool
            self.connection_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=CacheConfig.MAX_CONNECTIONS,
                retry_on_timeout=CacheConfig.RETRY_ON_TIMEOUT,
                socket_keepalive=CacheConfig.SOCKET_KEEPALIVE,
                socket_keepalive_options={},
                health_check_interval=30,
                decode_responses=False  # Handle encoding manually for better performance
            )
            
            self.redis_client = redis.Redis(
                connection_pool=self.connection_pool,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis cache service initialized successfully")
            
        except Exception as e:
            logger.error(f"Redis initialization failed: {e}")
            self.redis_client = None
    
    async def close(self):
        """Close Redis connections"""
        if self.redis_client:
            await self.redis_client.close()
        if self.connection_pool:
            await self.connection_pool.disconnect()
    
    def _generate_key(self, prefix: str, identifier: str, **kwargs) -> str:
        """Generate cache key with optional parameters"""
        key_parts = [prefix, identifier]
        
        if kwargs:
            # Sort kwargs for consistent key generation
            sorted_kwargs = sorted(kwargs.items())
            key_suffix = hashlib.md5(
                json.dumps(sorted_kwargs, sort_keys=True).encode()
            ).hexdigest()[:8]
            key_parts.append(key_suffix)
        
        return ":".join(key_parts)
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data for Redis storage"""
        try:
            # Use pickle for complex objects, JSON for simple ones
            if isinstance(data, (dict, list, str, int, float, bool)) and not isinstance(data, bytes):
                return json.dumps(data, default=str).encode('utf-8')
            else:
                return pickle.dumps(data)
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            return pickle.dumps(data)
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize data from Redis"""
        try:
            # Try JSON first (faster)
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            try:
                # Fall back to pickle
                return pickle.loads(data)
            except Exception as e:
                logger.error(f"Deserialization error: {e}")
                return None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get data from cache"""
        if not self.redis_client:
            return None
        
        try:
            data = await self.redis_client.get(key)
            if data:
                self.cache_stats["hits"] += 1
                return self._deserialize_data(data)
            else:
                self.cache_stats["misses"] += 1
                return None
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = CacheConfig.TTL_MEDIUM) -> bool:
        """Set data in cache with TTL"""
        if not self.redis_client:
            return False
        
        try:
            serialized_data = self._serialize_data(value)
            await self.redis_client.setex(key, ttl, serialized_data)
            self.cache_stats["sets"] += 1
            return True
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete data from cache"""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.delete(key)
            if result:
                self.cache_stats["deletes"] += 1
            return bool(result)
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                self.cache_stats["deletes"] += deleted
                return deleted
            return 0
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False
        
        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        redis_info = {}
        if self.redis_client:
            try:
                redis_info = await self.redis_client.info()
            except:
                pass
        
        return {
            "cache_stats": self.cache_stats,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
            "redis_info": {
                "connected_clients": redis_info.get("connected_clients", 0),
                "used_memory_human": redis_info.get("used_memory_human", "unknown"),
                "keyspace_hits": redis_info.get("keyspace_hits", 0),
                "keyspace_misses": redis_info.get("keyspace_misses", 0),
            }
        }
    
    # High-level caching methods for specific data types
    
    async def cache_project(self, project_id: int, project_data: Dict, ttl: int = CacheConfig.TTL_LONG):
        """Cache project data"""
        key = self._generate_key(CacheConfig.PREFIX_PROJECT, str(project_id))
        return await self.set(key, project_data, ttl)
    
    async def get_cached_project(self, project_id: int) -> Optional[Dict]:
        """Get cached project data"""
        key = self._generate_key(CacheConfig.PREFIX_PROJECT, str(project_id))
        return await self.get(key)
    
    async def cache_blog_post(self, post_id: int, post_data: Dict, ttl: int = CacheConfig.TTL_MEDIUM):
        """Cache blog post data"""
        key = self._generate_key(CacheConfig.PREFIX_BLOG, str(post_id))
        return await self.set(key, post_data, ttl)
    
    async def get_cached_blog_post(self, post_id: int) -> Optional[Dict]:
        """Get cached blog post data"""
        key = self._generate_key(CacheConfig.PREFIX_BLOG, str(post_id))
        return await self.get(key)
    
    async def cache_blog_list(self, filters: Dict, posts_data: List[Dict], ttl: int = CacheConfig.TTL_SHORT):
        """Cache blog post list with filters"""
        key = self._generate_key(CacheConfig.PREFIX_BLOG, "list", **filters)
        return await self.set(key, posts_data, ttl)
    
    async def get_cached_blog_list(self, filters: Dict) -> Optional[List[Dict]]:
        """Get cached blog post list"""
        key = self._generate_key(CacheConfig.PREFIX_BLOG, "list", **filters)
        return await self.get(key)
    
    async def cache_user_data(self, user_id: int, user_data: Dict, ttl: int = CacheConfig.TTL_MEDIUM):
        """Cache user data"""
        key = self._generate_key(CacheConfig.PREFIX_USER, str(user_id))
        return await self.set(key, user_data, ttl)
    
    async def get_cached_user_data(self, user_id: int) -> Optional[Dict]:
        """Get cached user data"""
        key = self._generate_key(CacheConfig.PREFIX_USER, str(user_id))
        return await self.get(key)
    
    async def cache_analytics_data(self, query_hash: str, analytics_data: Dict, ttl: int = CacheConfig.TTL_SHORT):
        """Cache analytics query results"""
        key = self._generate_key(CacheConfig.PREFIX_ANALYTICS, query_hash)
        return await self.set(key, analytics_data, ttl)
    
    async def get_cached_analytics_data(self, query_hash: str) -> Optional[Dict]:
        """Get cached analytics data"""
        key = self._generate_key(CacheConfig.PREFIX_ANALYTICS, query_hash)
        return await self.get(key)
    
    async def invalidate_blog_cache(self, post_id: Optional[int] = None):
        """Invalidate blog-related cache"""
        if post_id:
            # Invalidate specific post
            await self.delete(self._generate_key(CacheConfig.PREFIX_BLOG, str(post_id)))
        
        # Invalidate blog lists
        await self.delete_pattern(f"{CacheConfig.PREFIX_BLOG}list:*")
    
    async def invalidate_project_cache(self, project_id: Optional[int] = None):
        """Invalidate project-related cache"""
        if project_id:
            await self.delete(self._generate_key(CacheConfig.PREFIX_PROJECT, str(project_id)))
        else:
            await self.delete_pattern(f"{CacheConfig.PREFIX_PROJECT}*")

# Global cache instance
cache_service = CacheService()

def cached(ttl: int = CacheConfig.TTL_MEDIUM, key_prefix: str = CacheConfig.PREFIX_API):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_data = {
                "func": func.__name__,
                "args": str(args),
                "kwargs": str(sorted(kwargs.items()))
            }
            cache_key = cache_service._generate_key(key_prefix, func.__name__, **key_data)
            
            # Try to get from cache first
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            if result is not None:
                await cache_service.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

async def init_cache():
    """Initialize cache service"""
    await cache_service.initialize()

async def close_cache():
    """Close cache service"""
    await cache_service.close()