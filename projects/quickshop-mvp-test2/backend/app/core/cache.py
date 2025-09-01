"""
Redis cache configuration and utilities
"""

import redis.asyncio as redis
import json
import logging
from typing import Any, Optional, Union
from datetime import timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis connection pool
redis_pool: Optional[redis.ConnectionPool] = None
redis_client: Optional[redis.Redis] = None


async def init_redis():
    """Initialize Redis connection"""
    global redis_pool, redis_client
    
    try:
        redis_pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20
        )
        redis_client = redis.Redis(connection_pool=redis_pool)
        
        # Test connection
        await redis_client.ping()
        logger.info("Redis connection established")
        
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        redis_client = None
        redis_pool = None


async def get_redis() -> Optional[redis.Redis]:
    """Get Redis client"""
    if redis_client is None:
        await init_redis()
    return redis_client


async def close_redis():
    """Close Redis connection"""
    global redis_client, redis_pool
    
    if redis_client:
        await redis_client.close()
        redis_client = None
    
    if redis_pool:
        await redis_pool.disconnect()
        redis_pool = None


class CacheService:
    """Redis cache service"""
    
    def __init__(self):
        self.prefix = "quickshop:"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            client = await get_redis()
            if not client:
                return None
            
            value = await client.get(f"{self.prefix}{key}")
            if value:
                return json.loads(value)
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Union[int, timedelta] = 3600
    ) -> bool:
        """Set value in cache"""
        try:
            client = await get_redis()
            if not client:
                return False
            
            serialized_value = json.dumps(value, default=str)
            
            if isinstance(expire, timedelta):
                expire = int(expire.total_seconds())
            
            await client.setex(
                f"{self.prefix}{key}",
                expire,
                serialized_value
            )
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            client = await get_redis()
            if not client:
                return False
            
            result = await client.delete(f"{self.prefix}{key}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            client = await get_redis()
            if not client:
                return False
            
            result = await client.exists(f"{self.prefix}{key}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in cache"""
        try:
            client = await get_redis()
            if not client:
                return None
            
            result = await client.incrby(f"{self.prefix}{key}", amount)
            return result
            
        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return None
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key"""
        try:
            client = await get_redis()
            if not client:
                return False
            
            result = await client.expire(f"{self.prefix}{key}", seconds)
            return result
            
        except Exception as e:
            logger.error(f"Cache expire error: {e}")
            return False
    
    async def get_many(self, keys: list) -> dict:
        """Get multiple values from cache"""
        try:
            client = await get_redis()
            if not client:
                return {}
            
            prefixed_keys = [f"{self.prefix}{key}" for key in keys]
            values = await client.mget(prefixed_keys)
            
            result = {}
            for i, value in enumerate(values):
                if value:
                    try:
                        result[keys[i]] = json.loads(value)
                    except json.JSONDecodeError:
                        result[keys[i]] = value
                else:
                    result[keys[i]] = None
            
            return result
            
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            return {}
    
    async def set_many(self, mapping: dict, expire: int = 3600) -> bool:
        """Set multiple values in cache"""
        try:
            client = await get_redis()
            if not client:
                return False
            
            pipe = client.pipeline()
            for key, value in mapping.items():
                serialized_value = json.dumps(value, default=str)
                pipe.setex(f"{self.prefix}{key}", expire, serialized_value)
            
            await pipe.execute()
            return True
            
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern"""
        try:
            client = await get_redis()
            if not client:
                return 0
            
            keys = await client.keys(f"{self.prefix}{pattern}")
            if keys:
                result = await client.delete(*keys)
                return result
            return 0
            
        except Exception as e:
            logger.error(f"Cache clear_pattern error: {e}")
            return 0


# Create cache service instance
cache = CacheService()


# Cache decorators and utilities
def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    key_parts = []
    for arg in args:
        key_parts.append(str(arg))
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}:{v}")
    return ":".join(key_parts)


# Common cache keys
class CacheKeys:
    """Common cache key patterns"""
    
    USER_PROFILE = "user:profile:{user_id}"
    PRODUCT_DETAIL = "product:detail:{product_id}"
    PRODUCT_LIST = "product:list:{category}:{page}:{limit}"
    CART_ITEMS = "cart:items:{user_id}"
    ORDER_DETAIL = "order:detail:{order_id}"
    CATEGORY_LIST = "category:list"
    POPULAR_PRODUCTS = "product:popular:{limit}"
    SEARCH_RESULTS = "search:{query}:{page}:{limit}"
    
    @staticmethod
    def user_session(user_id: int) -> str:
        return f"session:user:{user_id}"
    
    @staticmethod
    def rate_limit(user_id: int, endpoint: str) -> str:
        return f"rate_limit:{user_id}:{endpoint}"